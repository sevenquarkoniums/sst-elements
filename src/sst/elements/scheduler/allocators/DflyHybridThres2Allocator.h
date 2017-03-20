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

#ifndef SST_SCHEDULER_DFLYHYBRIDTHRES2ALLOCATOR_H__
#define SST_SCHEDULER_DFLYHYBRIDTHRES2ALLOCATOR_H__

#include "DragonflyAllocator.h"

namespace SST {
    namespace Scheduler {

        class AllocInfo;
        class DragonFlyMachine;
        class Job;

        class DflyHybridThres2Allocator : public DragonflyAllocator {
            public:

                DflyHybridThres2Allocator(const DragonflyMachine & mach);

                ~DflyHybridThres2Allocator() { }

                std::string getSetupInfo(bool comment) const;

                AllocInfo* allocate(Job* j);

        };

    }
}
#endif // SST_SCHEDULER_DFLYHYBRIDTHRES2ALLOCATOR_H__
