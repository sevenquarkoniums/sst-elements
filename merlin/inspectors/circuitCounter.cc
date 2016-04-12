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
            setMap[key].uniquePaths = ps;
            uniquePaths = ps;
            setMap[key].circArrival = circArrival;
            setMap[key].setSize = setSize;
            isFirst = 1;
        } else {
            // someone else created the set already
            uniquePaths = iter->second.uniquePaths;
            circArrival = iter->second.circArrival;
            setSize = iter->second.setSize;
            isFirst = 0;
        }
        
        mapLock.unlock();
    }
}

void CircNetworkInspector::inspectNetworkData(SimpleNetwork::Request* req) {
    // this does not have to be locked since all the network
    // inspectors for a given router are serial
    auto inp = uniquePaths->insert(SDPair(req->src, req->dest));
    if (inp.second) { 
        // this a new insert
        uint64_t now = (uint64_t) nanoTimeConv->convertFromCoreTime(SST::Simulation::getSimulation()->getCurrentSimCycle());
        uint64_t diff = now - lastNew;
        circArrival->addData(diff);
        lastNew = now;
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
