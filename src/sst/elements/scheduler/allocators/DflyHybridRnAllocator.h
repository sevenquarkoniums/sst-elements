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
 * HybridRn allocator for Dragonfly machine which finds the lowest level
 * (switch/group/entire_machine) that a job can fit in, then spread
 * across that level.
 * For detail, see DragonflyHybridRnAllocator.cc.
 */

#ifndef SST_SCHEDULER_DFLYHYBRIDRNALLOCATOR_H__
#define SST_SCHEDULER_DFLYHYBRIDRNALLOCATOR_H__

#include "sst/core/rng/sstrng.h"

#include "DragonflyAllocator.h"

namespace SST {
    namespace Scheduler {

        class AllocInfo;
        class DragonFlyMachine;
        class Job;

        class DflyHybridRnAllocator : public DragonflyAllocator {
            public:

                DflyHybridRnAllocator(const DragonflyMachine & mach);

                ~DflyHybridRnAllocator();

                std::string getSetupInfo(bool comment) const;

                AllocInfo* allocate(Job* j);

            private:
                SST::RNG::SSTRandom* rng; //random number generator
        };

    }
}
#endif // SST_SCHEDULER_DFLYHYBRIDRNALLOCATOR_H__
