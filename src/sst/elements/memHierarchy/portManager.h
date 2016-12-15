// Copyright 2009-2016 Sandia Corporation. Under the terms
// of Contract DE-AC04-94AL85000 with Sandia Corporation, the U.S.
// Government retains certain rights in this software.
//
// Copyright (c) 2009-2016, Sandia Corporation
// All rights reserved.
//
// Portions are copyright of other developers:
// See the file CONTRIBUTORS.TXT in the top level directory
// the distribution for more information.
//
// This file is part of the SST software package. For license
// information, see the LICENSE file in the top level directory of the
// distribution.

#ifndef _MEMH_PORTMANAGER_H_
#define _MEMH_PORTMANAGER_H_

#include <queue>
#include <map>

#include <sst_config.h>
#include <sst/core/event.h>
#include <sst/core/sst_types.h>
#include <sst/core/subcomponent.h>
#include <sst/core/link.h>
#include <sst/core/timeConverter.h>
#include <sst/core/output.h>

#include "util.h"
#include "memEvent.h"
#include "memNIC.h"
#include <string>
#include <sstream>

namespace SST { namespace MemHierarchy {
using namespace std;

class CoherenceController;

class PortManager : public SST::SubComponent {

public:

    /* Constructors */
    PortManager();
    PortManager(Component * comp, Params &params);

    /* Event handler for external events */
    virtual void sendEventToPort(SST::Event * event);

    /* Communication back from cache controller */
    virtual void notifyEventConsumed(MemEvent::id_type id);
    
    virtual bool clock();

    /* Setup-related communication with cache */
    bool detectConfiguration();
    void init(unsigned int phase);
    bool bottomNetworkLinkExists();

    /* Send functions */
    void sendTowardsMem(MemEvent * event);
    void sendTowardsCPU(MemEvent * event);
    void setCoherenceManager(CoherenceController * ctrl) { coherenceMgr_ = ctrl; }

protected:
    /* Outputs */
    Output * output;
    Output * debug;
    
    /* Debug control */
    bool DEBUG_ALL;
    Addr DEBUG_ADDR;

    /* Links */
    MemNIC * bottomNetworkLink_;
    MemNIC * topNetworkLink_;
    Link * linkCPUBus_;
    Link * linkMemBus_;

    /* Pointer to coherence manager for statistics recording */
    // Statistics are a property of coherence protocol
    CoherenceController * coherenceMgr_;

private:
    /* Link configuration functions */
    void setupDirectMemSideLinks();
    void setupDirectCPUSideLink();
    void setupNetworkMemSideLink(std::string portname, Params &params);
    void setupSingleNetworkLink(Params &params);

}; // Class PortManager 
} // Namespace MemHierarchy
} // Namespace SST
#endif
