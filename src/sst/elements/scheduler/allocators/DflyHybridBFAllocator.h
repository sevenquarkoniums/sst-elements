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
 * Hybrid best-fit allocator for Dragonfly machine which finds the lowest level
 * (switch/group/entire_machine) that a job can fit in, then spread
 * across that level.
 */

#ifndef SST_SCHEDULER_DFLYHYBRIDBFALLOCATOR_H__
#define SST_SCHEDULER_DFLYHYBRIDBFALLOCATOR_H__

#include "DragonflyAllocator.h"

namespace SST {
    namespace Scheduler {

        class AllocInfo;
        class DragonFlyMachine;
        class Job;

        class DflyHybridBFAllocator : public DragonflyAllocator {
            public:

                DflyHybridBFAllocator(const DragonflyMachine & mach);

                ~DflyHybridBFAllocator() { }

                std::string getSetupInfo(bool comment) const;

                AllocInfo* allocate(Job* j);

        };

    }
}
#endif // SST_SCHEDULER_DFLYHYBRIDBFALLOCATOR_H__
