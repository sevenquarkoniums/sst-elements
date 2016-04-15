#include <sst_config.h>
#include "sst/core/serialization.h"
#include "sst/core/timeConverter.h"

#include "circuitCounter.h"

SST::Core::ThreadSafe::Spinlock CircNetworkInspector::mapLock;
CircNetworkInspector::setMap_t CircNetworkInspector::setMap;

CircNetworkInspector::CircNetworkInspector(SST::Component* parent, 
                                           SST::Params &params) :
    SimpleNetwork::NetworkInspector(parent), lastNew(0) {
    
    outFileName = params.find_string("output_file");
    if (outFileName.empty()) {
      outFileName = "RouterCircuits";
    }
    maxCircuits = params.find_integer("maxCircuits", 4);

    nanoTimeConv = SST::Simulation::getSimulation()->getTimeLord()->getTimeConverter("1ns");    
}

void CircNetworkInspector::initialize(string id) {
    // critical section for accessing the map
    {
        mapLock.lock();
        
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
            setMap[key].uniquePaths = ps;
            uniquePaths = ps;
            setMap[key].circArrival = circArrival;
            setMap[key].circMap = circMap;
            setMap[key].lruList = lruList;
            setMap[key].lruSpills = lruSpills;
            setMap[key].spillCount = spillCount;
            isFirst = 1;
        } else {
            // someone else created the set already
            uniquePaths = iter->second.uniquePaths;
            circArrival = iter->second.circArrival;
            lruSpills = iter->second.lruSpills;
            spillCount = iter->second.spillCount;
            setSize = iter->second.setSize;
            lruList = iter->second.lruList;
            circMap = iter->second.circMap;

            isFirst = 0;
        }

        mapLock.unlock();
    }
}

void CircNetworkInspector::inspectNetworkData(SimpleNetwork::Request* req) {
    // this does not have to be locked since all the network
    // inspectors for a given router are serial
    SDPair circ(req->src, req->dest);
    auto inp = uniquePaths->insert(circ);
    if (inp.second) { 
        // this a new insert
        uint64_t now = (uint64_t) nanoTimeConv->convertFromCoreTime(SST::Simulation::getSimulation()->getCurrentSimCycle());
        uint64_t diff = now - lastNew;
        circArrival->addData(diff);
        lastNew = now;
    } 


    // track the LRU list
    assert(lruList->size() == circMap->size());
    auto mapEntry = circMap->find(circ);
    if (mapEntry == circMap->end()) {
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
}

// Print out all the stats. We have the first component print all the
// stats and peform cleanup, everyone else finds an empty map.
void CircNetworkInspector::finish() {
    // critical section for accessing the map
    {
        mapLock.lock();
        
        if (!setMap.empty()) {
            // create new file
            SST::Output* output_file = new SST::Output("",0,0,
                                                       SST::Output::FILE, 
                                                       outFileName);
            
            for(setMap_t::iterator i = setMap.begin();
                i != setMap.end(); ++i) {
                // print
                output_file->output(CALL_INFO, "%s %" PRIu64 "\n", 
                                    i->first.c_str(), 
                                    (unsigned long long)i->second.uniquePaths->size());
                // clean up
                delete(i->second.uniquePaths);
                //delete(i->second.second);
            }
        }
        
        setMap.clear();
        
        mapLock.unlock();
    }
}
