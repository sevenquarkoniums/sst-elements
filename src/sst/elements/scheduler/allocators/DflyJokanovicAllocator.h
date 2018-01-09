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
 * Jokanovic's allocator for Dragonfly machine
 */

// file Factory.h Factory.cc Makefile.am should be modified.

#ifndef SST_SCHEDULER_DFLYJOKANOVICALLOCATOR_H__
#define SST_SCHEDULER_DFLYJOKANOVICALLOCATOR_H__

#include "DragonflyAllocator.h"

namespace SST {
    namespace Scheduler {

        class AllocInfo;
        class DragonFlyMachine;
        class Job;

        class DflyJokanovicAllocator : public DragonflyAllocator {
            public:

                DflyJokanovicAllocator(const DragonflyMachine & mach);

                ~DflyJokanovicAllocator() { }

                std::string getSetupInfo(bool comment) const;

                AllocInfo* allocate(Job* j);

        };

    }
}
#endif // SST_SCHEDULER_DFLYJOKANOVICALLOCATOR_H__
