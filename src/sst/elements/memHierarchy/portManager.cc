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


#include <sst_config.h>
#include <sst/core/link.h>

#include "sst/elements/memHierarchy/util.h"
#include "portManager.h"
#include "cacheController.h"
#include "coherenceController.h"
#include "memNIC.h"
#include <sst/core/interfaces/stringEvent.h>

using namespace SST;
using namespace SST::MemHierarchy;

PortManager::PortManager(Component *comp, Params &params) : SubComponent(comp) {
    /* Output stream */
    output = new Output("", 1, 0, SST::Output::STDOUT);
    /* Debug stream */
    debug = new Output("", params.find<int>("debug_level", 1), 0, (Output::output_location_t)params.find<int>("debug", SST::Output::NONE));
    int64_t dAddr = params.find<int64_t>("debug_addr", -1);
    if (dAddr != -1) DEBUG_ALL = false;
    else DEBUG_ALL = true;
    DEBUG_ADDR = (Addr)dAddr;
    
    /* Setup links - our 'real' ports (not cache ports) */
    /* Detect port configuration */
    bool directConnectCPUSide       = isPortConnected("high_network_0");    // Cache or bus connected directly (cpu-side)
    bool directConnectMemSide       = isPortConnected("low_network_0");     // Cache or bus connected directly (mem-side)
    bool networkConnectedCache      = isPortConnected("cache");             // cache connected over network
    bool networkConnectedDirectory  = isPortConnected("directory");         // directory connected over network

    /* Check for valid configuration */
    if (directConnectCPUSide) {
        if (!networkConnectedCache && !networkConnectedDirectory && !directConnectMemSide)
            output->fatal(CALL_INFO,-1,"%s, Error: no connected low (memory-side) ports detected. Please connect one of 'cache' or 'directory' or 'low_network_0'\n",
                    comp->getName().c_str());
        if ((networkConnectedCache && (networkConnectedDirectory || directConnectMemSide)) || (networkConnectedDirectory && directConnectMemSide))  
            output->fatal(CALL_INFO,-1,"%s, Error: multiple connected low (memory-side) port types detected. Use only one type of port: 'cache', 'directory' or 'low_network_0'. Detected ports: 'cache'=%s, 'directory'=%s, 'low_network_0'=%s\n",
                    comp->getName().c_str(), networkConnectedCache ? "true" : "false", networkConnectedDirectory ? "true" : "false", directConnectMemSide ? "true" : "false");
        if (isPortConnected("high_network_1"))
            output->fatal(CALL_INFO,-1,"%s, Error: multiple connected high (cpu-side) ports detected. Use the 'Bus' component to connect multiple entities to port 'high_network_0' (e.g., connect 2 L1s to a bus and connect the bus to the L2)\n",
                    comp->getName().c_str());
        if (isPortConnected("low_network_1"))
            output->fatal(CALL_INFO,-1,"%s, Error: multiple connected low (memory-side) ports detected. Use the 'Bus' component to connect multiple entities to port 'low_network_0' (e.g., connect L1 to multiple L2 slices)\n",
                    comp->getName().c_str());
    } else {
        if (!networkConnectedDirectory) 
            output->fatal(CALL_INFO,-1,"%s, Error: no connected ports detected. Valid ports are high_network_0, cache, directory, and low_network_0\n",
                    comp->getName().c_str());
        if (networkConnectedCache || directConnectMemSide)
            output->fatal(CALL_INFO,-1,"%s, Error: no connected high (cpu-side) ports detected. Please connect a bus/cache/core on port 'high_network_0'\n",
                    comp->getName().c_str());
    }
    
    /* null all the link pointers */
    bottomNetworkLink_ = nullptr;
    topNetworkLink_ = nullptr;
    linkCPUBus_ = nullptr;
    linkMemBus_ = nullptr;

    /* Configure the links */
    if (directConnectCPUSide && directConnectMemSide) {
        debug->debug(_INFO_,"Configuring cache with a direct link above and one or more direct links below.\n");
        setupDirectMemSideLinks();
        setupDirectCPUSideLink();
    } else if (directConnectCPUSide && networkConnectedCache) {
        debug->debug(_INFO_,"Configuring cache with a direct link above and a network link to a cache below\n");
        setupNetworkMemSideLink("cache", params);
        setupDirectCPUSideLink();
        
    } else if (directConnectCPUSide && networkConnectedDirectory) {
        debug->debug(_INFO_,"Configuring cache with a direct link above and a network link to a directory below\n");
        setupNetworkMemSideLink("directory", params);
        setupDirectCPUSideLink();

    } else {    // networkConnectedDirectory
        debug->debug(_INFO_, "Configuring cache with a single network link to talk to a cache above and a directory below\n");
        setupSingleNetworkLink(params);
    }
}


/* 
 *  Incoming event handler 
 *  Call through to cache
 */

void PortManager::sendEventToPort(SST::Event* ev) {
    MemEvent* event = static_cast<MemEvent*>(ev);
    debug->debug(_L8_, "Port received event: Addr = 0x%" PRIx64 ", Cmd = %s.\n", event->getBaseAddr(), CommandString[event->getCmd()]);
    static_cast<Cache*>(parent)->notifyReadyEvent(event);
}

void PortManager::notifyEventConsumed(MemEvent::id_type id) { }

bool PortManager::clock() {
    if (bottomNetworkLink_) return bottomNetworkLink_->clock();
    return true;
}

void PortManager::sendTowardsMem(MemEvent * event) {
    debug->debug(_L8_, "Port sendTowardsMem Event: Addr = 0x%" PRIx64 ", Cmd = %s.\n", event->getBaseAddr(), CommandString[event->getCmd()]);
    coherenceMgr_->recordEventSentDown(event->getCmd()); 
    if (bottomNetworkLink_) {
        event->setDst(bottomNetworkLink_->findTargetDestination(event->getBaseAddr()));
        bottomNetworkLink_->send(event);
    } else {
        linkMemBus_->send(event);
    }
}

void PortManager::sendTowardsCPU(MemEvent * event) {
    debug->debug(_L8_, "Port sendTowardsCPU Event: Addr = 0x%" PRIx64 ", Cmd = %s.\n", event->getBaseAddr(), CommandString[event->getCmd()]);
    coherenceMgr_->recordEventSentUp(event->getCmd()); 
    if (topNetworkLink_) {
        topNetworkLink_->send(event);
    } else {
        linkCPUBus_->send(event);
    }
}

/* Configure links */
void PortManager::setupDirectMemSideLinks() {
    // Configure low links
    SST::Link * link = configureLink("low_network_0", "50ps", new Event::Handler<PortManager>(this, &PortManager::sendEventToPort));
    debug->debug(_INFO_, "Low Network Link ID: %u\n", (uint)link->getId());
    linkMemBus_ = link;
    bottomNetworkLink_ = NULL;
}

void PortManager::setupDirectCPUSideLink() {
    // Configure high link
    SST::Link * link = configureLink("high_network_0", "50ps", new Event::Handler<PortManager>(this, &PortManager::sendEventToPort));
    debug->debug(_INFO_, "High Network Link ID: %u\n", (uint)link->getId());
    linkCPUBus_ = link;
    topNetworkLink_ = NULL;
}


void PortManager::setupNetworkMemSideLink(std::string portname, Params& params) {
    // Configure low link
    MemNIC::ComponentInfo myInfo;
    myInfo.link_port = portname;
    myInfo.link_bandwidth = params.find<std::string>("network_bw", "80GiB/s");
    myInfo.num_vcs = 1;
    myInfo.name = parent->getName();
    myInfo.network_addr = params.find<int>("network_address");
    myInfo.type = (portname == "cache") ? MemNIC::TypeCacheToCache : MemNIC::TypeCache; 
    myInfo.link_inbuf_size = params.find<std::string>("network_input_buffer_size", "1KiB");
    myInfo.link_outbuf_size = params.find<std::string>("network_output_buffer_size", "1KiB");

    MemNIC::ComponentTypeInfo typeInfo;
    typeInfo.blocksize = static_cast<Cache*>(parent)->getLineSize();
    typeInfo.coherenceProtocol = static_cast<Cache*>(parent)->getProtocol();
    typeInfo.cacheType = static_cast<Cache*>(parent)->getCacheType();

    bottomNetworkLink_ = new MemNIC(parent, debug, DEBUG_ADDR, myInfo, new Event::Handler<PortManager>(this, &PortManager::sendEventToPort));
    bottomNetworkLink_->addTypeInfo(typeInfo);
    UnitAlgebra packet = UnitAlgebra(params.find<std::string>("min_packet_size", "8B"));
    if (!packet.hasUnits("B")) 
        output->fatal(CALL_INFO, -1, "%s, Invalid param: min_packet_size - must have units of bytes (B). Ex: '8B'. SI units are ok. You specified '%s'\n", 
                parent->getName().c_str(), packet.toString().c_str());
    bottomNetworkLink_->setMinPacketSize(packet.getRoundedValue());
}


void PortManager::setupSingleNetworkLink(Params &params) {
    // Configure low link
    // This NIC may need to account for cache slices. Check params.
    int cacheSliceCount         = params.find<int>("num_cache_slices", 1);
    int sliceID                 = params.find<int>("slice_id", 0);
    string sliceAllocPolicy     = params.find<std::string>("slice_allocation_policy", "rr");
    if (cacheSliceCount == 1) sliceID = 0;
    else if (cacheSliceCount > 1) {
        if (sliceID >= cacheSliceCount) output->fatal(CALL_INFO,-1, "%s, Invalid param: slice_id - should be between 0 and num_cache_slices-1. You specified %d.\n",
                parent->getName().c_str(), sliceID);
        if (sliceAllocPolicy != "rr") output->fatal(CALL_INFO,-1, "%s, Invalid param: slice_allocation_policy - supported policy is 'rr' (round-robin). You specified '%s'.\n",
                parent->getName().c_str(), sliceAllocPolicy.c_str());
    } else {
        output->fatal(CALL_INFO, -1, "%s, Invalid param: num_cache_slices - should be 1 or greater. You specified %d.\n", 
                parent->getName().c_str(), cacheSliceCount);
    }

    MemNIC::ComponentInfo myInfo;
    myInfo.link_port = "directory";
    myInfo.link_bandwidth = params.find<std::string>("network_bw", "80GiB/s");
    myInfo.num_vcs = 1;
    myInfo.name = parent->getName();
    myInfo.network_addr = params.find<int>("network_address");
    myInfo.type = MemNIC::TypeNetworkCache; 
    myInfo.link_inbuf_size = params.find<std::string>("network_input_buffer_size", "1KiB");
    myInfo.link_outbuf_size = params.find<std::string>("network_output_buffer_size", "1KiB");
    MemNIC::ComponentTypeInfo typeInfo;
    uint64_t addrRangeStart = 0;
    uint64_t addrRangeEnd = (uint64_t)-1;
    uint64_t interleaveSize = 0;
    uint64_t interleaveStep = 0;
    if (cacheSliceCount > 1) {
        if (sliceAllocPolicy == "rr") {
            interleaveSize = static_cast<Cache*>(parent)->getLineSize();
            addrRangeStart = sliceID * interleaveSize;
            interleaveStep = cacheSliceCount * interleaveSize;
        }
        static_cast<Cache*>(parent)->setSliceAware(cacheSliceCount);
    }
    typeInfo.rangeStart     = addrRangeStart;
    typeInfo.rangeEnd       = addrRangeEnd;
    typeInfo.interleaveSize = interleaveSize;
    typeInfo.interleaveStep = interleaveStep;
    typeInfo.blocksize      = static_cast<Cache*>(parent)->getLineSize();
    typeInfo.coherenceProtocol = static_cast<Cache*>(parent)->getProtocol();
    typeInfo.cacheType = static_cast<Cache*>(parent)->getCacheType();
        
    bottomNetworkLink_ = new MemNIC(parent, debug, DEBUG_ADDR, myInfo, new Event::Handler<PortManager>(this, &PortManager::sendEventToPort));
    bottomNetworkLink_->addTypeInfo(typeInfo);
    UnitAlgebra packet = UnitAlgebra(params.find<std::string>("min_packet_size", "8B"));
    if (!packet.hasUnits("B")) 
        output->fatal(CALL_INFO, -1, "%s, Invalid param: min_packet_size - must have units of bytes (B). Ex: '8B'. SI units are ok. You specified '%s'\n", 
                parent->getName().c_str(), packet.toString().c_str());
    bottomNetworkLink_->setMinPacketSize(packet.getRoundedValue());

    // Configure high link
    topNetworkLink_ = bottomNetworkLink_;
}


/*
 *  Handle init traffic on the links
 *  1. Pass on cache type (inclusive, noninclusive, etc.)
 *  2. Collect names of possible destinations for network links
 */
void PortManager::init(unsigned int phase) {
    // See if we can determine whether the lower entity is non-inclusive
    if (topNetworkLink_) { // I'm connected to the network ONLY via a single NIC
        bottomNetworkLink_->init(phase);
            
        /*  */
        while(MemEvent *event = bottomNetworkLink_->recvInitData()) {
            delete event;
        }
        return;
    }
    
    SST::Event *ev;
    if (bottomNetworkLink_) {
        bottomNetworkLink_->init(phase);
    }
    
    if (!phase) {
        if (static_cast<Cache*>(parent)->isL1()) {
            linkCPUBus_->sendInitData(new Interfaces::StringEvent("SST::MemHierarchy::MemEvent"));
        } else {
            if (static_cast<Cache*>(parent)->getCacheType() == "inclusive") {
                linkCPUBus_->sendInitData(new MemEvent(parent, 0, 0, NULLCMD));
            } else {
                linkCPUBus_->sendInitData(new MemEvent(parent, 1, 0, NULLCMD));
            }
        }
        if (!bottomNetworkLink_) {
            linkMemBus_->sendInitData(new MemEvent(parent, 10, 10, NULLCMD));
        }
        
    }

    while ((ev = linkCPUBus_->recvInitData())) {
        MemEvent* memEvent = dynamic_cast<MemEvent*>(ev);
        if (!memEvent) { /* Do nothing */ }
        else if (memEvent->getCmd() == NULLCMD) {
            if (memEvent->getCmd() == NULLCMD) {    // Save upper level cache names
                static_cast<Cache*>(parent)->addUpperLevelCacheName(memEvent->getSrc());
            }
        } else {
            if (bottomNetworkLink_) {
                bottomNetworkLink_->sendInitData(new MemEvent(*memEvent));
            } else {
                linkMemBus_->sendInitData(new MemEvent(*memEvent));
            }
        }
        delete memEvent;
     }
    
    if (!bottomNetworkLink_) {  // Save names of caches below us
        while ((ev = linkMemBus_->recvInitData())) {
            MemEvent* memEvent = dynamic_cast<MemEvent*>(ev);
            if (memEvent && memEvent->getCmd() == NULLCMD) {
                if (memEvent->getBaseAddr() == 0) {
                    static_cast<Cache*>(parent)->setLL(false);
                    if (memEvent->getAddr() == 1) {
                        static_cast<Cache*>(parent)->setLowerIsNoninclusive(true); // TODO better checking if we have multiple caches below us
                    }
                }
                static_cast<Cache*>(parent)->addLowerLevelCacheName(memEvent->getSrc());
            }
            delete memEvent;
        }
    }
}

/* Help the cache with auto-detect around init messages */
bool PortManager::detectConfiguration() {
    bool isDirBelow = false; // is a directory below?
    if (bottomNetworkLink_) {
        static_cast<Cache*>(parent)->setLL(false);  // Either a directory or a cache below us TODO what about a memory?
        static_cast<Cache*>(parent)->setLowerIsNoninclusive(false);
        isDirBelow = true; // Assume a directory is below
        const std::vector<MemNIC::PeerInfo_t> &ci = bottomNetworkLink_->getPeerInfo();
        const MemNIC::ComponentInfo &myCI = bottomNetworkLink_->getComponentInfo();
        // Search peer info to determine if we have inclusive or noninclusive caches below us
        if (MemNIC::TypeCacheToCache == myCI.type) { // I'm a cache with a cache below
            isDirBelow = false; // Cache not directory below us
            for (std::vector<MemNIC::PeerInfo_t>::const_iterator i = ci.begin() ; i != ci.end() ; ++i) {
                if (MemNIC::TypeNetworkCache == i->first.type) { // This would be any cache that is 'below' us
                    if (i->second.cacheType != "inclusive") {
                        static_cast<Cache*>(parent)->setLowerIsNoninclusive(true);
                    }
                }
            }
        }
    }
    return isDirBelow;
}

bool PortManager::bottomNetworkLinkExists() {
    return bottomNetworkLink_ != nullptr;
}
