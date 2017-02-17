// Copyright 2009-2015 Sandia Corporation. Under the terms
// of Contract DE-AC04-94AL85000 with Sandia Corporation, the U.S.
// Government retains certain rights in this software.
// 
// Copyright (c) 2009-2015, Sandia Corporation
// All rights reserved.
// 
// This file is part of the SST software package. For license
// information, see the LICENSE file in the top level directory of the
// distribution.

#include "sst_config.h"
#include "sst/core/rng/mersenne.h"

#include "DflyRRNAllocator.h"

#include "AllocInfo.h"
#include "DragonflyMachine.h"
#include "Job.h"

using namespace SST::Scheduler;

DflyRRNAllocator::DflyRRNAllocator(const DragonflyMachine & mach)
  : DragonflyAllocator(mach)
{
    rng = new SST::RNG::MersenneRNG();
}

DflyRRNAllocator::~DflyRRNAllocator()
{
    delete rng;
}

std::string DflyRRNAllocator::getSetupInfo(bool comment) const
{
    std::string com;
    if (comment) {
        com = "# ";
    } else {
        com = "";
    }
    return com + "Dragonfly Round Robin Nodes Allocator";
}

#include <iostream>
using namespace std;

AllocInfo* DflyRRNAllocator::allocate(Job* j)
{
    if (canAllocate(*j)) {
        AllocInfo* ai = new AllocInfo(j, dMach);
        //This set keeps track of allocated nodes in the current allocation.
        std::set<int> occupiedNodes;
        const int jobSize = ai->getNodesNeeded();
        const int routerNum = dMach.routersPerGroup * dMach.numGroups;
        std::cout << "jobSize = " << jobSize << ", allocation, ";
        int i = 0;
        while (i < jobSize) {
            //randomly choose a router.
            int routerID = rng->generateNextUInt32() % routerNum;
            //select all nodes in this router.
            for (int localNodeID = 0; localNodeID < dMach.nodesPerRouter; localNodeID++) {
                int nodeID = routerID * dMach.nodesPerRouter + localNodeID;
                if ( dMach.isFree(nodeID) && occupiedNodes.find(nodeID) == occupiedNodes.end() ) {
                    ai->nodeIndices[i] = nodeID;
                    ++i;
                    occupiedNodes.insert(nodeID);
                    std::cout << nodeID << " ";
                }
                else {
                    continue;
                }
                if (i == jobSize) {
                    break;
                }
            }
        }
        std::cout << endl;
        return ai;
    }
    return NULL;
}

