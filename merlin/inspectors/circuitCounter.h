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

using namespace std;
using namespace SST::Interfaces;

class CircNetworkInspector : public SimpleNetwork::NetworkInspector {
private:
    typedef pair<SimpleNetwork::nid_t, SimpleNetwork::nid_t> SDPair;
    typedef set<SDPair> pairSet_t;
    pairSet_t *uniquePaths;
    string outFileName;
    SST::TimeConverter* nanoTimeConv;
    uint64_t lastNew;
    Statistic<uint64_t>*  circArrival;
    Statistic<uint64_t>*  setSize;
    bool isFirst; // is the first port in the router

    // per router data
    struct routerData {
        pairSet_t *uniquePaths;
        Statistic<uint64_t> *circArrival;
        Statistic<uint64_t> *setSize;
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

#endif
