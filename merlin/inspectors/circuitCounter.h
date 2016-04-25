// Copyright 2016 Sandia Corporation. Under the terms
// of Contract DE-AC04-94AL85000 with Sandia Corporation, the U.S.
// Government retains certain rights in this software.
//
// Copyright (c) 2015, Sandia Corporation
// All rights reserved.
//
// This file is part of the SST software package. For license
// information, see the LICENSE file in the top level directory of the
// distribution.

#ifndef COMPONENTS_MERLIN_CIRCUITCOUNTER_H
#define COMPONENTS_MERLIN_CIRCUITCOUNTER_H

#include <sst/core/subcomponent.h>
#include <sst/core/interfaces/simpleNetwork.h>
#include <sst/core/threadsafe.h>
#include <sst/core/timeLord.h>
#include <sst/core/element.h>

using namespace std;
using namespace SST::Interfaces;

class CircNetworkInspector : public SimpleNetwork::NetworkInspector {
private:
    typedef pair<SimpleNetwork::nid_t, SimpleNetwork::nid_t> SDPair;
    typedef set<SDPair> pairSet_t;
    typedef list<SDPair> pairList_t;
    typedef map<SDPair, pairList_t::iterator> circMap_t;
    pairSet_t *uniquePaths_epoch;
    pairSet_t *uniquePaths;
    string outFileName;
    int maxCircuits;
    SST::TimeConverter* nanoTimeConv;
    uint64_t lastNew;
    Statistic<uint64_t>*  circArrival;
    Statistic<uint64_t>*  setSize;
    Statistic<uint64_t>*  lruSpills;
    int* spillCount;
    pairList_t *lruList;
    map<SDPair, pairList_t::iterator> *circMap;
    bool isFirst; // is the first port in the router

    SST::Clock::HandlerBase *ClockHandler;
    SST::TimeConverter *tickC; 
    bool tick(SST::Cycle_t);

    // per router data
    struct routerData {
        pairSet_t *uniquePaths_epoch;
        pairSet_t *uniquePaths;
        Statistic<uint64_t> *circArrival;
        Statistic<uint64_t> *setSize;
        Statistic<uint64_t> *lruSpills;
        int *spillCount;
        pairList_t *lruList;
        map<SDPair, pairList_t::iterator> *circMap;
    };
    
    typedef map<string, routerData> setMap_t;
    // Map which makes sure that all the inspectors on one router use
    // the same pairSet. This structure can be accessed by multiple
    // threads during intiailize, so it needs to be protected.
    static setMap_t setMap;
    static SST::Core::ThreadSafe::Spinlock mapLock;
public:
    CircNetworkInspector(SST::Component* parent, SST::Params &params);

    void initialize(string id);
    void finish();

    void inspectNetworkData(SimpleNetwork::Request* req);
};

static const SST::ElementInfoParam circ_network_params[] = {
    { "output_file", "file to output circult list to", "stdout"},
    { "maxCircuits", "max number of circuits to model with LRU replacement", "4"},
    { NULL, NULL, NULL}
};

static const SST::ElementInfoStatistic circ_network_statistics[] = {
    {"circuitArrival", "Time between 'arrival' of a new circuit", "ns", 1},
    {"setSize", "Size of the set of unique circuits", "", 1},
    {"lruSpills", "Number of circuits spilled from the LRU cache of circuits", "", 1},
    { NULL, NULL, NULL, 0}
};

#endif
