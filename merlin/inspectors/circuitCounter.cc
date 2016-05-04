#include <sst_config.h>
#include "sst/core/serialization.h"
#include "sst/core/timeConverter.h"

#include "hr_router/hr_router.h"
#include "topology/fattree.h"
#include "circuitCounter.h"

using SST::Merlin::hr_router;
using SST::Merlin::topo_fattree;

SST::Core::ThreadSafe::Spinlock CircNetworkInspector::mapLock;
CircNetworkInspector::setMap_t CircNetworkInspector::setMap;
std::map<int,int> CircNetworkInspector::topo;

//sst --model-options="--topo=torus --shape=6x6x12  --platform=optic --rtrArb=xbar_arb_lru_infx --netInspect="merlin.circuit_network_inspector" --netInspectParams="maxCircuits=32,circuitSetup=100" --cmdLine=\"Init\" --cmdLine=\"FFT3D npRow=16\" --cmdLine=\"Fini\"" emberLoad_circ.py

CircNetworkInspector::CircNetworkInspector(SST::Component* parent, 
                                           SST::Params &params) :
    SimpleNetwork::NetworkInspector(parent), lastNew(0) {
    
    outFileName = params.find_string("output_file");
    if (outFileName.empty()) {
        outFileName = "";
    }
    maxCircuits = params.find_integer("maxCircuits", 16);

    circuitSetup = params.find_integer("circuitSetup", 0);

    nanoTimeConv = SST::Simulation::getSimulation()->getTimeLord()->getTimeConverter("1ns");    

    // register a clock
    ClockHandler = new SST::Clock::Handler<CircNetworkInspector>(this, 
                                                                 &CircNetworkInspector::tick);
    assert(ClockHandler);
    tickC = registerClock("100 ms", ClockHandler);
    assert(tickC);

}

void CircNetworkInspector::initialize(string id) {
    // critical section for accessing the map
    {
        mapLock.lock();
        
        topo_fattree *ft = 0;
        hr_router *hr = dynamic_cast<hr_router*>(parent);
        if (hr) {
            ft = dynamic_cast<topo_fattree*>(hr->topo);
            if (ft) {
                topo[ft->rtr_level] = ft->down_ports;
            }
        }

        // use router name as the key
        const string &key = parent->getName();
        // look up our key
        setMap_t::iterator iter = setMap.find(key);
        if (iter == setMap.end()) {
            // we're first!
            pairSet_t *ps = new pairSet_t;
            circArrival = registerStatistic<uint64_t>("circuitArrival", "1");
            setSize = registerStatistic<uint64_t>("setSize", "1");
            lruSpills = registerStatistic<uint64_t>("lruSpills", "1");
            spillCount = new int(0);
            lruList = new pairList_t;
            circMap = new circMap_t;
            uniquePaths_epoch = (setMap[key].uniquePaths_epoch = new pairSet_t);
            setMap[key].uniquePaths = ps;
            uniquePaths = ps;
            setMap[key].circArrival = circArrival;
            setMap[key].circMap = circMap;
            setMap[key].lruList = lruList;
            setMap[key].lruSpills = lruSpills;
            setMap[key].spillCount = spillCount;
            if (ft) {
                setMap[key].rtr_level = ft->rtr_level;
            } else {
                setMap[key].rtr_level = 0;
            }
            isFirst = 1;
        } else {
            // someone else created the set already
            uniquePaths_epoch = iter->second.uniquePaths_epoch;
            uniquePaths = iter->second.uniquePaths;
            circArrival = iter->second.circArrival;
            lruSpills = iter->second.lruSpills;
            spillCount = iter->second.spillCount;
            setSize = iter->second.setSize;
            lruList = iter->second.lruList;
            circMap = iter->second.circMap;

            // only the 'first' does this
            unregisterClock(tickC, ClockHandler);

            isFirst = 0;
        }

        mapLock.unlock();
    }
}

bool CircNetworkInspector::tick( SST::Cycle_t ) {
    if (isFirst) {

        SST::Output* output_file = new SST::Output("",0,0,
                                                   SST::Output::STDOUT);
        
        output_file->output(CALL_INFO, "RC:%" PRIu64 " %s %" PRIu64 "\n", 
                            getCurrentSimTimeMicro()/1000, 
                            parent->getName().c_str(), 
                            (unsigned long long)uniquePaths_epoch->size());
        
        uniquePaths_epoch->clear();
    }
    return false;
}

int CircNetworkInspector::inspectNetworkData(SimpleNetwork::Request* req) {
    // this does not have to be locked since all the network
    // inspectors for a given router are serial
    SDPair circ(req->src, req->dest);
    uint64_t now = (uint64_t) nanoTimeConv->convertFromCoreTime(SST::Simulation::getSimulation()->getCurrentSimCycle());

    uniquePaths_epoch->insert(circ);
    auto inp = uniquePaths->insert(circ);
    if (inp.second) { 
        // this a new insert
        uint64_t diff = now - lastNew;
        circArrival->addData(diff);
        lastNew = now;
    } 


    // track the LRU list
    assert(lruList->size() == circMap->size());
    bool newCircuit = false;
    auto mapEntry = circMap->find(circ);
    if (mapEntry == circMap->end()) {
        newCircuit = true;
        // not alread in the list
        if (circMap->size() < maxCircuits) {
            // just insert          
            lruList->push_back(circ);
            circMap->operator[](circ) = (--lruList->end());
            assert(circMap->find(circ) != circMap->end());
        } else {
            // kick someone out...
            SDPair &victim = lruList->front();
            assert(circMap->find(victim) != circMap->end());
            circMap->erase(victim);
            lruList->pop_front();
            lruSpills->addData(1);
            (*spillCount)++;
            // ...and insert
            lruList->push_back(circ);
            circMap->operator[](circ) = (--lruList->end());
            assert(lruList->size() == circMap->size());
        }
    } else {
        // one we've seen before. move to back of LRU list
        // remove from LRU list
        lruList->erase(mapEntry->second);
        // place in back
        lruList->push_back(circ);
        // update map
        circMap->operator[](circ) = (--lruList->end());
    }

    if(isFirst) {
        // only the 'first' port adds to this data
        setSize->addData(uniquePaths->size());
    }

    int delay = 0;
    if (newCircuit) {
        circTime[circ] = now + circuitSetup;
        delay = circuitSetup;
    } else {
        auto ci = circTime.find(circ);
        if (ci == circTime.end()) {
            assert(0);
        } else {            
            delay = max(int64_t(0), ci->second - int64_t(now));
        }
    }

    return delay;
}

// Print out all the stats. We have the first component print all the
// stats and peform cleanup, everyone else finds an empty map.
void CircNetworkInspector::finish() {
    // critical section for accessing the map
    {
        mapLock.lock();
        
        if (!setMap.empty()) {
            // create new file
            SST::Output* output_file;
            if (outFileName.empty()) {
                output_file = new SST::Output("",0,0,
                                              SST::Output::STDOUT);
            } else {
                output_file = new SST::Output("",0,0,
                                              SST::Output::FILE, 
                                              outFileName);
            }
            
            for(setMap_t::iterator i = setMap.begin();
                i != setMap.end(); ++i) {
                // print
                output_file->output(CALL_INFO, "RC %s %" PRIu64 " %d\n", 
                                    i->first.c_str(), 
                                    (unsigned long long)i->second.uniquePaths->size(), 
                                    uniquePathsBelow(i->second.uniquePaths, 
                                                     i->second.rtr_level));
                // clean up
                delete(i->second.uniquePaths);
                delete(i->second.uniquePaths_epoch);
                //delete(i->second.second);
            }
        }
        
        setMap.clear();
        
        mapLock.unlock();
    }
}

int CircNetworkInspector::uniquePathsBelow(const pairSet_t *ups, int rtrLvl) {
    if (topo.empty()) {
        return ups->size();
    }

    int divisor = 1;
    map<int,int>::iterator ii = topo.end();
    ii--;
    int highestLevel = ii->first;
    for (int c = rtrLvl+1; c <= highestLevel; ++c) {
        divisor = divisor * topo[c];
        if (divisor == 0) {
            return ups->size();
        }
    }

    pairSet_t newSet;
    for(pairSet_t::iterator i = ups->begin();
        i != ups->end(); ++i) {
        SDPair p = *i;
        p.first /= divisor;
        p.second /= divisor;
        newSet.insert(p);
    }

    return int(newSet.size());
}
