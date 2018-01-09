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

#include "DflyHybridThres2Allocator.h"

#include "AllocInfo.h"
#include "DragonflyMachine.h"
#include "Job.h"

using namespace SST::Scheduler;

DflyHybridThres2Allocator::DflyHybridThres2Allocator(const DragonflyMachine & mach)
  : DragonflyAllocator(mach)
{

}

std::string DflyHybridThres2Allocator::getSetupInfo(bool comment) const
{
    std::string com;
    if (comment) {
        com = "# ";
    } else {
        com = "";
    }
    return com + "Dragonfly HybridThres2 Allocator";
}

#include <iostream>
using namespace std;

AllocInfo* DflyHybridThres2Allocator::allocate(Job* j)
{
    if (canAllocate(*j)) {
        AllocInfo* ai = new AllocInfo(j, dMach);
        //This set keeps track of allocated nodes in the current allocation.
        std::set<int> occupiedNodes;
        const int jobSize = ai->getNodesNeeded();
        std::cout << "jobSize=" << jobSize << ", ";
        if (jobSize <= dMach.nodesPerRouter) {
            //find the router with the most free nodes.
            int BestRouter = -1;
            int BestRouterFreeNodes = 0;
            for (int routerID = 0; routerID < dMach.numRouters; routerID++) {
                int thisRouterFreeNode = 0;
                for (int localNodeID = 0; localNodeID < dMach.nodesPerRouter; localNodeID++) {
                    int nodeID = routerID * dMach.nodesPerRouter + localNodeID;
                    if ( dMach.isFree(nodeID) && occupiedNodes.find(nodeID) == occupiedNodes.end() ) {
                        //caution: isFree() will update only after one job is fully allocated.
                        ++thisRouterFreeNode;
                    }
                }
                if (thisRouterFreeNode > BestRouterFreeNodes) {
                    BestRouter = routerID;
                    BestRouterFreeNodes = thisRouterFreeNode;
                }
            }
            //if job can fit in this router, then 
            //we allocate the job to this router simply.
            if (jobSize <= BestRouterFreeNodes) {
                int nodeID = BestRouter * dMach.nodesPerRouter;
                int i = 0;
                while (i < jobSize) {
                    if ( dMach.isFree(nodeID) && occupiedNodes.find(nodeID) == occupiedNodes.end() ) {
                        ai->nodeIndices[i] = nodeID;
                        occupiedNodes.insert(nodeID);
                        std::cout << nodeID << " ";
                        ++i;
                        ++nodeID;
                    }
                    else {
                        ++nodeID;
                    }
                }
                std::cout << endl;
                return ai;
            }
        }
        int nodesPerGroup = dMach.routersPerGroup * dMach.nodesPerRouter;
        //Threshold changed. If job fits in 2 groups, then do simple allocation.
        if (jobSize <= 2 * nodesPerGroup) {
            //find the group with the most free nodes.
            int BestGroup = -1;
            int BestGroupFreeNodes = 0;
            for (int GroupID = 0; GroupID < dMach.numGroups; GroupID++) {
                int thisGroupFreeNode = 0;
                for (int localNodeID = 0; localNodeID < nodesPerGroup; localNodeID++) {
                    int nodeID = GroupID * nodesPerGroup + localNodeID;
                    if ( dMach.isFree(nodeID) && occupiedNodes.find(nodeID) == occupiedNodes.end() ) {
                        ++thisGroupFreeNode;
                    }
                }
                if (thisGroupFreeNode > BestGroupFreeNodes) {
                    BestGroup = GroupID;
                    BestGroupFreeNodes = thisGroupFreeNode;
                }
            }
            //we allocate the job starting from this group simply.
            int startNode = BestGroup * nodesPerGroup;
            int nodeID = startNode;
            for (int i = 0; i < jobSize; i++) {
                while (true) {
                    if ( dMach.isFree(nodeID) && occupiedNodes.find(nodeID) == occupiedNodes.end() ) {
                        ai->nodeIndices[i] = nodeID;
                        occupiedNodes.insert(nodeID);
                        std::cout << nodeID << " ";
                        //change node.
                        if (nodeID < dMach.numNodes - 1) {
                            ++nodeID;
                        }
                        else {
                            nodeID = 0;
                        }
                        break;
                    }
                    else {
                        //move to next node.
                        if (nodeID < dMach.numNodes - 1) {
                            ++nodeID;
                        }
                        else {
                            nodeID = 0;
                        }
                        continue;
                    }
                }
            }
            std::cout << endl;
            return ai;
        }
        //job cannot fit,
        //it will simply spread across the machine.
        int groupID = 0;
        for (int i = 0; i < jobSize; i++) {
            int localNodeID = 0;
            while (true) {
                int nodeID = groupID * nodesPerGroup + localNodeID;
                if ( dMach.isFree(nodeID) && occupiedNodes.find(nodeID) == occupiedNodes.end() ) {
                    ai->nodeIndices[i] = nodeID;
                    occupiedNodes.insert(nodeID);
                    std::cout << nodeID << " ";
                    //change group.
                    if (groupID < dMach.numGroups - 1) {
                        ++groupID;
                    }
                    else {
                        groupID = 0;
                    }
                    break;
                }
                else {
                    if (localNodeID < nodesPerGroup - 1) {
                        ++localNodeID;
                        continue;
                    }
                    else {
                        //change group.
                        if (groupID < dMach.numGroups - 1) {
                            ++groupID;
                        }
                        else {
                            groupID = 0;
                        }
                        localNodeID = 0;
                        continue;
                    }
                }
            }
        }
        std::cout << endl;
        return ai;
    }
    return NULL;
}
