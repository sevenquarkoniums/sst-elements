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

/*
 * Hybrid allocator for Dragonfly machine which finds the lowest level
 * (switch/group/entire_machine) that a job can fit in, then spread
 * across that level.
 * For detail, see DragonflyHybridAllocator.cc.
 */

// file Factory.h Factory.cc Makefile.am should be modified.

#ifndef SST_SCHEDULER_DRAGONFLYHYBRIDALLOCATOR_H__
#define SST_SCHEDULER_DRAGONFLYHYBRIDALLOCATOR_H__

#include "DragonflyAllocator.h"

namespace SST {
    namespace Scheduler {

        class AllocInfo;
        class DragonFlyMachine;
        class Job;

        class DragonflyHybridAllocator : public DragonflyAllocator {
            public:

                DragonflyHybridAllocator(const DragonflyMachine & mach);

                ~DragonflyHybridAllocator() { }

                std::string getSetupInfo(bool comment) const;

                AllocInfo* allocate(Job* j);

            private:

                bool notAllocated(int nodeID);

                //keep track of occupied nodes in one process of allocation.
                std::set<int> occupiedNodes;
        };

    }
}
#endif // SST_SCHEDULER_DRAGONFLYHYBRIDALLOCATOR_H__
