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
#include "portManagerMulti.h"
#include "cacheController.h"
#include "memEvent.h"

using namespace SST;
using namespace SST::MemHierarchy;

PortManagerMulti::PortManagerMulti(Component * comp, Params &params) : PortManager(comp, params) {
    
    output->output("Output initialized...\n");
    
    /* Get port count */
    uint32_t portCount = params.find<uint32_t>("port_count", 1);
    if (portCount < 1) {
        output->fatal(CALL_INFO, -1, "%s, Invalid param: port_count - must be at least 1. You specified '%d'.\n", comp->getName().c_str(), portCount);
    }

    /* Get port params */
    std::list<uint32_t> rPorts;
    std::list<uint32_t> wPorts;
    std::list<uint32_t> rwPorts;
    for (uint32_t i = 0; i < portCount; i++) {
        std::string search = std::to_string(i);
        /* Ports are defined as '%d.param' */
        std::string pType = params.find<std::string>(search + ".type", "rw");
        std::string pWidth = params.find<std::string>(search + ".width", "64B");

        UnitAlgebra pWidth_ua(pWidth);
        if (!pWidth_ua.hasUnits("B")) {
            output->fatal(CALL_INFO, -1, "%s, Invalid param: port.%s.width - must have units of bytes ('B'). Ex: '64B'. You specified '%s'.\n", comp->getName().c_str(), search.c_str(), pWidth.c_str());
        }
        if (pWidth_ua.getRoundedValue() < 1) {
            output->fatal(CALL_INFO, -1, "%s, Invalid param: port.%s.width - must be at least 1B. You sepcified '%s'.\n", comp->getName().c_str(), search.c_str(), pWidth.c_str());
        }

        if (pType == "r") rPorts.push_back(pWidth_ua.getRoundedValue());
        else if (pType == "w") wPorts.push_back(pWidth_ua.getRoundedValue());
        else if (pType == "rw") rwPorts.push_back(pWidth_ua.getRoundedValue());
        else {
            output->fatal(CALL_INFO, 01, "%s, Invalid param: port.%s.type - must be one of 'r' (read), 'w' (write), or 'rw' (read-write). You specified '%s'\n", comp->getName().c_str(), search.c_str(), pType.c_str());
        }
    }

    /* Sanity check - these are valid combinations but excepting read-only L1 I-caches, could be a configuration error */
    if (rPorts.empty() && rwPorts.empty()) {
        output->output("%s, NOTICE: No read or read-write ports detected. Cache will be write-only.\n", comp->getName().c_str());
    }
    if (wPorts.empty() && rwPorts.empty()) {
        output->output("%s, NOTICE: No write or read-write ports detected. Cache will be read-only.\n", comp->getName().c_str());
    }

    rPorts.sort();
    wPorts.sort();
    rwPorts.sort();
    
    /* Now put in decreasing-size order in the actual port queues */
    /* Currently we have one queue per port type, this should be ok if the number of ports is small 
     * If it grows, may need to implement separate pools for ports in different states to avoid iterating over port lists TODO */
    while (!rPorts.empty()) {
        readPorts_.push_back(CachePort(rPorts.front(), CachePort::Status::Free, nullptr));
        rPorts.pop_front();
    }
    while (!wPorts.empty()) {
        writePorts_.push_back(CachePort(wPorts.front(), CachePort::Status::Free, nullptr));
        wPorts.pop_front();
    }
    while (!rwPorts.empty()) {
        readWritePorts_.push_back(CachePort(rwPorts.front(), CachePort::Status::Free, nullptr));
        rwPorts.pop_front();
    }

    /* Set up self link for delaying requests that are larger than a port */
    std::string clock = params.find<std::string>("clock");  // Cache gives us this parameter and ensures it is set correctly, no error checking here
    portDelaySelfLink_ = configureSelfLink("portDelayLink", clock, new Event::Handler<PortManagerMulti>(this, &PortManagerMulti::unblockPort));

    /* Slight difference in GetX handling, L1 handles as a write while all others handle as a read */
    L1_ = params.find<bool>("L1", false);

    /* Re-configure link handlers to our own */
    if (linkCPUBus_) linkCPUBus_->setFunctor(new Event::Handler<PortManagerMulti>(this, &PortManagerMulti::sendEventToPort));
    if (linkMemBus_) linkMemBus_->setFunctor(new Event::Handler<PortManagerMulti>(this, &PortManagerMulti::sendEventToPort));
    if (bottomNetworkLink_) bottomNetworkLink_->setRecvHandler(new Event::Handler<PortManagerMulti>(this, &PortManagerMulti::sendEventToPort));
}

void PortManagerMulti::sendEventToPort(SST::Event * ev) {
    MemEvent * event = static_cast<MemEvent*>(ev);    
    
    switch(event->getCmd()) {
        /* Read requests */
        case GetS:
        case GetSEx:
            if (!placeEventOnReadPort(event, true)) bufferedEvents_.push(std::make_pair(event, "r"));
            break;
        /* May be read or write depending on L1 or not */
        case GetX:
            if (L1_) {
                if (!placeEventOnWritePort(event, true)) bufferedEvents_.push(std::make_pair(event, "w"));
            } else {
                if (!placeEventOnReadPort(event, true)) bufferedEvents_.push(std::make_pair(event, "r"));
            }
            break;
        /* Write requests */
        case FlushLine:
        case FlushLineInv:
        case FlushAll:
        case PutS:
        case PutM:
        case PutE:
            if (!placeEventOnWritePort(event, true)) bufferedEvents_.push(std::make_pair(event, "w"));
            break;
        /* Data responses & coherence events with data */
        case FetchResp:
        case FetchXResp:
        case GetSResp:
        case GetXResp:
            static_cast<Cache*>(parent)->notifyReadyEvent(event);
            break;
        /* Coherence requests */
        case Inv:
        case Fetch:
        case FetchInv:
        case FetchInvX:
            static_cast<Cache*>(parent)->notifyReadyEvent(event);
            break;
        /* Coherence responses without data */
        case NACK:
        case FlushLineResp:
        case FlushAllResp:
        case AckInv:
        case AckPut:
            static_cast<Cache*>(parent)->notifyReadyEvent(event);
            break;
        default:
            output->fatal(CALL_INFO, -1, "%s, PortManager received an event with command '%s' and does not have handling implemented for this command type.\n", parent->getName().c_str(), CommandString[event->getCmd()]);
    }
}


void PortManagerMulti::unblockPort(SST::Event * ev) {
    PortMgrEvent * event = static_cast<PortMgrEvent*>(ev);
    if (event->type_ == "r") {
        readPorts_[event->index_].status_ = CachePort::Status::Ready;
        static_cast<Cache*>(parent)->notifyReadyEvent(readPorts_[event->index_].event_);
    } else if (event->type_ == "w") {
        writePorts_[event->index_].status_ = CachePort::Status::Ready;
        static_cast<Cache*>(parent)->notifyReadyEvent(writePorts_[event->index_].event_);
    } else if (event->type_ == "rw") {
        readWritePorts_[event->index_].status_ = CachePort::Status::Ready;
        static_cast<Cache*>(parent)->notifyReadyEvent(readWritePorts_[event->index_].event_);
    }
    delete event;
}

void PortManagerMulti::notifyEventConsumed(MemEvent::id_type id) {
    PortPointer ptr = readyEvents_.find(id)->second;
    
    if (ptr.type_ == "r") {
        readPorts_[ptr.index_].status_ = CachePort::Status::Free;
    } else if (ptr.type_ == "w") {
        writePorts_[ptr.index_].status_ = CachePort::Status::Free;
    } else if (ptr.type_ == "rw") {
        readWritePorts_[ptr.index_].status_ = CachePort::Status::Free;
    }
    readyEvents_.erase(id);

    /* Check if we have buffered events, and add to nowReadyEvents_ if possible */
    while (!bufferedEvents_.empty()) {
        if (bufferedEvents_.front().second == "r") {
            if (placeEventOnReadPort(bufferedEvents_.front().first, false)) {
                bufferedEvents_.pop();
            } else break;
        } else {
            if (placeEventOnWritePort(bufferedEvents_.front().first, false)) {
                bufferedEvents_.pop();
            } else break;
        }
    }
}

bool PortManagerMulti::clock() {
    bool idle = true;
    if (bottomNetworkLink_) idle = bottomNetworkLink_->clock();

    while (!nowReadyEvents_.empty()) {
        static_cast<Cache*>(parent)->notifyReadyEvent(nowReadyEvents_.front());
        nowReadyEvents_.pop();
        idle = false;
    }
    return idle; // If false, ok to turn off clock
}

bool PortManagerMulti::placeEventOnReadPort(MemEvent * event, bool immediateCallback) {
    /* Search read ports first */
    int readID = findReadPort(event->getSize());


    /* No free read ports, check read-write ports */
    if (readID == -1) {
        int readwriteID = findReadWritePort(event->getSize());
        if (readwriteID == -1) return false; /* No available read or read-write ports */
        if (readWritePorts_[readwriteID].size_ >= event->getSize()) {
            readWritePorts_[readwriteID].event_ = event;
            readWritePorts_[readwriteID].status_ = CachePort::Status::Ready;
            readyEvents_.insert(std::make_pair(event->getID(), PortPointer("rw", readwriteID)));
            if (immediateCallback) {
                static_cast<Cache*>(parent)->notifyReadyEvent(event);
            } else {
                nowReadyEvents_.push(event);
            }
        } else {
            readWritePorts_[readwriteID].event_ = event;
            readWritePorts_[readwriteID].status_ = CachePort::Status::Blocked;
            uint64_t delay = event->getSize() / readWritePorts_[readwriteID].size_ + ( event->getSize() % readWritePorts_[readwriteID].size_ == 0 ? 0 : 1);
            portDelaySelfLink_->send(delay, new PortMgrEvent("rw", readwriteID));
        }
        return true;
    }

    /* Found a read port and it is big enough */
    if (readPorts_[readID].size_ >= event->getSize()) {
        readPorts_[readID].event_ = event;
        readPorts_[readID].status_ = CachePort::Status::Ready;
        readyEvents_.insert(std::make_pair(event->getID(), PortPointer("r", readID)));
        if (immediateCallback) {
            static_cast<Cache*>(parent)->notifyReadyEvent(event);
        } else {
            nowReadyEvents_.push(event);
        }
        return true;
    }

    int readwriteID = findReadWritePort(event->getSize());

    /* Use read port even if too small */
    if (readwriteID == -1 || (readPorts_[readID].size_ >= readWritePorts_[readwriteID].size_)) {
        readPorts_[readID].event_ = event;
        readPorts_[readID].status_ = CachePort::Status::Blocked;
        uint64_t delay = event->getSize() / readPorts_[readID].size_ + ( event->getSize() % readPorts_[readID].size_ == 0 ? 0 : 1);
        portDelaySelfLink_->send(delay, new PortMgrEvent("r", readID));
    }

    /* Use read-write port */
    if (readWritePorts_[readwriteID].size_ >= event->getSize()) {
        readWritePorts_[readwriteID].event_ = event;
        readWritePorts_[readwriteID].status_ = CachePort::Status::Ready;
        readyEvents_.insert(std::make_pair(event->getID(), PortPointer("rw", readwriteID)));
        if (immediateCallback) {
            static_cast<Cache*>(parent)->notifyReadyEvent(event);
        } else {
            nowReadyEvents_.push(event);
        }
    } else {
        readWritePorts_[readwriteID].event_ = event;
        readWritePorts_[readwriteID].status_ = CachePort::Status::Blocked;
        uint64_t delay = event->getSize() / readWritePorts_[readwriteID].size_ + ( event->getSize() % readWritePorts_[readwriteID].size_ == 0 ? 0 : 1);
        portDelaySelfLink_->send(delay, new PortMgrEvent("rw", readwriteID));
    }
    return true;
}


bool PortManagerMulti::placeEventOnWritePort(MemEvent * event, bool immediateCallback) {
    /* Search write ports first */
    int writeID = findWritePort(event->getSize());

    /* No free write ports, check read-write ports */
    if (writeID == -1) {
        int readwriteID = findReadWritePort(event->getSize());
        if (readwriteID == -1) return false; /* No available read or read-write ports */
        if (readWritePorts_[readwriteID].size_ >= event->getSize()) {
            readWritePorts_[readwriteID].event_ = event;
            readWritePorts_[readwriteID].status_ = CachePort::Status::Ready;
            readyEvents_.insert(std::make_pair(event->getID(), PortPointer("rw", readwriteID)));
            if (immediateCallback) {
                static_cast<Cache*>(parent)->notifyReadyEvent(event);
            } else {
                nowReadyEvents_.push(event);
            }
        } else {
            readWritePorts_[readwriteID].event_ = event;
            readWritePorts_[readwriteID].status_ = CachePort::Status::Blocked;
            uint64_t delay = event->getSize() / readWritePorts_[readwriteID].size_ + ( event->getSize() % readWritePorts_[readwriteID].size_ == 0 ? 0 : 1);
            portDelaySelfLink_->send(delay, new PortMgrEvent("rw", readwriteID));
        }
        return true;
    }

    /* Found a write port and it is big enough */
    if (writePorts_[writeID].size_ >= event->getSize()) {
        writePorts_[writeID].event_ = event;
        writePorts_[writeID].status_ = CachePort::Status::Ready;
        readyEvents_.insert(std::make_pair(event->getID(), PortPointer("w", writeID)));
        if (immediateCallback) {
            static_cast<Cache*>(parent)->notifyReadyEvent(event);
        } else {
            nowReadyEvents_.push(event);
        }
        return true;
    }

    int readwriteID = findReadWritePort(event->getSize());

    /* Use write port even if too small */
    if (readwriteID == -1 || (writePorts_[writeID].size_ >= readWritePorts_[readwriteID].size_)) {
        writePorts_[writeID].event_ = event;
        writePorts_[writeID].status_ = CachePort::Status::Blocked;
        uint64_t delay = event->getSize() / writePorts_[writeID].size_ + ( event->getSize() % writePorts_[writeID].size_ == 0 ? 0 : 1);
        portDelaySelfLink_->send(delay, new PortMgrEvent("w", writeID));
    }

    /* Use read-write port */
    if (readWritePorts_[readwriteID].size_ >= event->getSize()) {
        readWritePorts_[readwriteID].event_ = event;
        readWritePorts_[readwriteID].status_ = CachePort::Status::Ready;
        readyEvents_.insert(std::make_pair(event->getID(), PortPointer("rw", readwriteID)));
        if (immediateCallback) {
            static_cast<Cache*>(parent)->notifyReadyEvent(event);
        } else {
            nowReadyEvents_.push(event);
        }
    } else {
        readWritePorts_[readwriteID].event_ = event;
        readWritePorts_[readwriteID].status_ = CachePort::Status::Blocked;
        uint64_t delay = event->getSize() / readWritePorts_[readwriteID].size_ + ( event->getSize() % readWritePorts_[readwriteID].size_ == 0 ? 0 : 1);
        portDelaySelfLink_->send(delay, new PortMgrEvent("rw", readwriteID));
    }
}

int PortManagerMulti::findReadPort(uint32_t size) {
    int index = -1;
    for (int i = 0; i < readPorts_.size(); i++) {
        if (readPorts_[i].status_ == CachePort::Status::Free) {
            index = i;
            if (readPorts_[i].size_ >= size) break;
        }
    }
    return index;
}

int PortManagerMulti::findWritePort(uint32_t size) {
    int index = -1;
    for (int i = 0; i < writePorts_.size(); i++) {
        if (writePorts_[i].status_ == CachePort::Status::Free) {
            index = i;
            if (writePorts_[i].size_ >= size) break;
        }
    }
    return index;

}

int PortManagerMulti::findReadWritePort(uint32_t size) {
    int index = -1;
    for (int i = 0; i < readWritePorts_.size(); i++) {
        if (readWritePorts_[i].status_ == CachePort::Status::Free) {
            index = i;
            if (readWritePorts_[i].size_ >= size) break;
        }
    }
    return index;
}
