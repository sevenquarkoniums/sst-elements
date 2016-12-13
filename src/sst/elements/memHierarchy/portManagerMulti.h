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

#ifndef _MEMH_PORTMANAGERMULTI_H_
#define _MEMH_PORTMANAGERMULTI_H_

#include <queue>
#include <map>

#include <sst/core/event.h>
#include <sst/core/sst_types.h>
#include <sst/core/subcomponent.h>
#include <sst/core/link.h>
#include <sst/core/timeConverter.h>
#include <sst/core/output.h>

#include "portManager.h"
#include "util.h"
#include "memEvent.h"
#include <string>
#include <sstream>

namespace SST { namespace MemHierarchy {
using namespace std;

class PortManagerMulti : public PortManager {

public:

    /* Constructors */
    PortManagerMulti(Component * comp, Params &params);

    /* Event handler for external events */
    void sendEventToPort(SST::Event * event);

    /* Event handler for unblock (self) events */
    void unblockPort(SST::Event * event);

    /* Communication back from cache controller */
    void notifyEventConsumed(MemEvent::id_type id);
    
    bool clock();

private:
    /* Cache port type */
    class CachePort {
    
        public:
            typedef enum {Free, Ready, Blocked } Status;
            
            uint32_t size_;     // Port size in bytes
            Status status_; // Status of port
            MemEvent * event_;  // Event currently on the port

            CachePort(uint32_t size, Status status, MemEvent * event) : size_(size), status_(status), event_(event) {}
    };

    /* Used when we need to record a pointer to a port */
    class PortPointer {
        public:
            int index_;
            std::string type_;
            PortPointer(std::string type, int index) : type_(type), index_(index) { }
            PortPointer() { }
    };

    /* Event with a port pointer, used for delaying an event on a port */
    class PortMgrEvent : public SST::Event {
        public:
            PortMgrEvent( std::string type, int index) : SST::Event(), type_(type), index_(index) {}
            std::string type_;
            int index_;
        
            NotSerializable(PortMgrEvent)
    };

    /* 
     * List of ports - currently vectors because the number of ports is assumed to be low 
     */
    std::vector<CachePort> readPorts_;
    std::vector<CachePort> writePorts_;
    std::vector<CachePort> readWritePorts_;

    /* Events that are available ('Ready') on ports */
    std::map<MemEvent::id_type, PortPointer> readyEvents_;

    /* Events that have been buffered and which type of event it is */
    std::queue< std::pair<MemEvent*, std::string> > bufferedEvents_;
    std::queue< MemEvent*> nowReadyEvents_;

    /* Self link for delaying requests on narrow links */
    Link * portDelaySelfLink_;

    /* Outputs */
    Output * output;
    Output * debug;
    
    /* L1 */
    bool L1_;

    /* Place events on ports */
    bool placeEventOnReadPort(MemEvent * event, bool immediateCallback);
    bool placeEventOnWritePort(MemEvent * event, bool immediateCallback);
    bool placeEventOnResponsePort(MemEvent * event);

    /* Search for available ports */
    int findReadPort(uint32_t size);
    int findReadWritePort(uint32_t size);
    int findWritePort(uint32_t size);
}; // Class PortManagerMulti
} // Namespace MemHierarchy
} // Namespace SST
#endif
