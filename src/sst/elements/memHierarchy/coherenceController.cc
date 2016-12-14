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

#include "coherenceController.h"

using namespace SST;
using namespace SST::MemHierarchy;


CoherenceController::CoherenceController(Component * comp, Params &params) : SubComponent(comp) {
    /* Output stream */
    output = new Output("", 1, 0, SST::Output::STDOUT);

    /* Debug stream */
    debug = new Output("--->  ", params.find<int>("debug_level", 1), 0, (Output::output_location_t)params.find<int>("debug", SST::Output::NONE));

    bool found;

    /* Get latency parameters */
    accessLatency_ = params.find<uint64_t>("access_latency_cycles", 1, found);
    if (!found) {
        output->fatal(CALL_INFO, -1, "%s, Param not specified: access_latency_cycles - this is the access time in cycles for the cache; if tag_latency is also specified, this is the data array access time\n",
                comp->getName().c_str());
    }

    tagLatency_ = params.find<uint64_t>("tag_access_latency_cycles", accessLatency_);
    mshrLatency_ = params.find<uint64_t>("mshr_latency", 1); /* cacheFactory is currently checking/setting this for us */

    /* Get line size - already error checked by cacheFactory */
    lineSize_ = params.find<unsigned int>("cache_line_size", 64, found);

    /* Initialize variables */
    timestamp_ = 0;

    // Register statistics - only those that are common across all coherence managers
    // TODO move many of these to individual coherence protocol managers
    stat_evict_I =      registerStatistic<uint64_t>("evict_I");
    stat_evict_E =      registerStatistic<uint64_t>("evict_E");
    stat_evict_M =      registerStatistic<uint64_t>("evict_M");
    stat_evict_IS =     registerStatistic<uint64_t>("evict_IS");
    stat_evict_IM =     registerStatistic<uint64_t>("evict_IM");
    stat_evict_IB =     registerStatistic<uint64_t>("evict_IB");
    stat_evict_SB =     registerStatistic<uint64_t>("evict_SB");

        stat_stateEvent_GetS_I =    registerStatistic<uint64_t>("stateEvent_GetS_I");
        stat_stateEvent_GetS_S =    registerStatistic<uint64_t>("stateEvent_GetS_S");
        stat_stateEvent_GetS_E =    registerStatistic<uint64_t>("stateEvent_GetS_E");
        stat_stateEvent_GetS_M =    registerStatistic<uint64_t>("stateEvent_GetS_M");
        stat_stateEvent_GetX_I =    registerStatistic<uint64_t>("stateEvent_GetX_I");
        stat_stateEvent_GetX_S =    registerStatistic<uint64_t>("stateEvent_GetX_S");
        stat_stateEvent_GetX_E =    registerStatistic<uint64_t>("stateEvent_GetX_E");
        stat_stateEvent_GetX_M =    registerStatistic<uint64_t>("stateEvent_GetX_M");
        stat_stateEvent_GetSEx_I =  registerStatistic<uint64_t>("stateEvent_GetSEx_I");
        stat_stateEvent_GetSEx_S =  registerStatistic<uint64_t>("stateEvent_GetSEx_S");
        stat_stateEvent_GetSEx_E =  registerStatistic<uint64_t>("stateEvent_GetSEx_E");
        stat_stateEvent_GetSEx_M =  registerStatistic<uint64_t>("stateEvent_GetSEx_M");
        stat_stateEvent_GetSResp_IS =       registerStatistic<uint64_t>("stateEvent_GetSResp_IS");
        stat_stateEvent_GetSResp_IM =       registerStatistic<uint64_t>("stateEvent_GetSResp_IM");
        stat_stateEvent_GetSResp_SM =       registerStatistic<uint64_t>("stateEvent_GetSResp_SM");
        stat_stateEvent_GetSResp_SMInv =    registerStatistic<uint64_t>("stateEvent_GetSResp_SMInv");
        stat_stateEvent_GetXResp_IM =       registerStatistic<uint64_t>("stateEvent_GetXResp_IM");
        stat_stateEvent_GetXResp_SM =       registerStatistic<uint64_t>("stateEvent_GetXResp_SM");
        stat_stateEvent_GetXResp_SMInv =    registerStatistic<uint64_t>("stateEvent_GetXResp_SMInv");
        stat_stateEvent_PutS_I =    registerStatistic<uint64_t>("stateEvent_PutS_I");
        stat_stateEvent_PutS_S =    registerStatistic<uint64_t>("stateEvent_PutS_S");
        stat_stateEvent_PutS_E =    registerStatistic<uint64_t>("stateEvent_PutS_E");
        stat_stateEvent_PutS_M =    registerStatistic<uint64_t>("stateEvent_PutS_M");
        stat_stateEvent_PutS_SD =   registerStatistic<uint64_t>("stateEvent_PutS_SD");
        stat_stateEvent_PutS_ED =   registerStatistic<uint64_t>("stateEvent_PutS_ED");
        stat_stateEvent_PutS_MD =   registerStatistic<uint64_t>("stateEvent_PutS_MD");
        stat_stateEvent_PutS_SMD =  registerStatistic<uint64_t>("stateEvent_PutS_SMD");
        stat_stateEvent_PutS_SI =   registerStatistic<uint64_t>("stateEvent_PutS_SI");
        stat_stateEvent_PutS_EI =   registerStatistic<uint64_t>("stateEvent_PutS_EI");
        stat_stateEvent_PutS_MI =   registerStatistic<uint64_t>("stateEvent_PutS_MI");
        stat_stateEvent_PutS_SInv = registerStatistic<uint64_t>("stateEvent_PutS_SInv");
        stat_stateEvent_PutS_EInv = registerStatistic<uint64_t>("stateEvent_PutS_EInv");
        stat_stateEvent_PutS_MInv = registerStatistic<uint64_t>("stateEvent_PutS_MInv");
        stat_stateEvent_PutS_SMInv =    registerStatistic<uint64_t>("stateEvent_PutS_SMInv");
        stat_stateEvent_PutS_EInvX =    registerStatistic<uint64_t>("stateEvent_PutS_EInvX");
        stat_stateEvent_PutE_I =    registerStatistic<uint64_t>("stateEvent_PutE_I");
        stat_stateEvent_PutE_E =    registerStatistic<uint64_t>("stateEvent_PutE_E");
        stat_stateEvent_PutE_M =    registerStatistic<uint64_t>("stateEvent_PutE_M");
        stat_stateEvent_PutE_EI =   registerStatistic<uint64_t>("stateEvent_PutE_EI");
        stat_stateEvent_PutE_MI =   registerStatistic<uint64_t>("stateEvent_PutE_MI");
        stat_stateEvent_PutE_EInv = registerStatistic<uint64_t>("stateEvent_PutE_EInv");
        stat_stateEvent_PutE_MInv = registerStatistic<uint64_t>("stateEvent_PutE_MInv");
        stat_stateEvent_PutE_EInvX =    registerStatistic<uint64_t>("stateEvent_PutE_EInvX");
        stat_stateEvent_PutE_MInvX =    registerStatistic<uint64_t>("stateEvent_PutE_MInvX");
        stat_stateEvent_PutM_I =    registerStatistic<uint64_t>("stateEvent_PutM_I");
        stat_stateEvent_PutM_E =    registerStatistic<uint64_t>("stateEvent_PutM_E");
        stat_stateEvent_PutM_M =    registerStatistic<uint64_t>("stateEvent_PutM_M");
        stat_stateEvent_PutM_EI =   registerStatistic<uint64_t>("stateEvent_PutM_EI");
        stat_stateEvent_PutM_MI =   registerStatistic<uint64_t>("stateEvent_PutM_MI");
        stat_stateEvent_PutM_EInv = registerStatistic<uint64_t>("stateEvent_PutM_EInv");
        stat_stateEvent_PutM_MInv = registerStatistic<uint64_t>("stateEvent_PutM_MInv");
        stat_stateEvent_PutM_EInvX =    registerStatistic<uint64_t>("stateEvent_PutM_EInvX");
        stat_stateEvent_PutM_MInvX =    registerStatistic<uint64_t>("stateEvent_PutM_MInvX");
        stat_stateEvent_Inv_I =     registerStatistic<uint64_t>("stateEvent_Inv_I");
        stat_stateEvent_Inv_IS =    registerStatistic<uint64_t>("stateEvent_Inv_IS");
        stat_stateEvent_Inv_IM =    registerStatistic<uint64_t>("stateEvent_Inv_IM");
        stat_stateEvent_Inv_S =     registerStatistic<uint64_t>("stateEvent_Inv_S");
        stat_stateEvent_Inv_SM =    registerStatistic<uint64_t>("stateEvent_Inv_SM");
        stat_stateEvent_Inv_SInv =  registerStatistic<uint64_t>("stateEvent_Inv_SInv");
        stat_stateEvent_Inv_SI =    registerStatistic<uint64_t>("stateEvent_Inv_SI");
        stat_stateEvent_Inv_SMInv = registerStatistic<uint64_t>("stateEvent_Inv_SMInv");
        stat_stateEvent_Inv_SD =    registerStatistic<uint64_t>("stateEvent_Inv_SD");
        stat_stateEvent_FetchInv_I =    registerStatistic<uint64_t>("stateEvent_FetchInv_I");
        stat_stateEvent_FetchInv_IS =   registerStatistic<uint64_t>("stateEvent_FetchInv_IS");
        stat_stateEvent_FetchInv_IM =   registerStatistic<uint64_t>("stateEvent_FetchInv_IM");
        stat_stateEvent_FetchInv_SM =   registerStatistic<uint64_t>("stateEvent_FetchInv_SM");
        stat_stateEvent_FetchInv_S =    registerStatistic<uint64_t>("stateEvent_FetchInv_S");
        stat_stateEvent_FetchInv_E =    registerStatistic<uint64_t>("stateEvent_FetchInv_E");
        stat_stateEvent_FetchInv_M =    registerStatistic<uint64_t>("stateEvent_FetchInv_M");
        stat_stateEvent_FetchInv_EI =   registerStatistic<uint64_t>("stateEvent_FetchInv_EI");
        stat_stateEvent_FetchInv_MI =   registerStatistic<uint64_t>("stateEvent_FetchInv_MI");
        stat_stateEvent_FetchInv_EInv = registerStatistic<uint64_t>("stateEvent_FetchInv_EInv");
        stat_stateEvent_FetchInv_EInvX =    registerStatistic<uint64_t>("stateEvent_FetchInv_EInvX");
        stat_stateEvent_FetchInv_MInv = registerStatistic<uint64_t>("stateEvent_FetchInv_MInv");
        stat_stateEvent_FetchInv_MInvX =    registerStatistic<uint64_t>("stateEvent_FetchInv_MInvX");
        stat_stateEvent_FetchInv_SD =   registerStatistic<uint64_t>("stateEvent_FetchInv_SD");
        stat_stateEvent_FetchInv_ED =   registerStatistic<uint64_t>("stateEvent_FetchInv_ED");
        stat_stateEvent_FetchInv_MD =   registerStatistic<uint64_t>("stateEvent_FetchInv_MD");
        stat_stateEvent_FetchInvX_I =   registerStatistic<uint64_t>("stateEvent_FetchInvX_I");
        stat_stateEvent_FetchInvX_IS =  registerStatistic<uint64_t>("stateEvent_FetchInvX_IS");
        stat_stateEvent_FetchInvX_IM =  registerStatistic<uint64_t>("stateEvent_FetchInvX_IM");
        stat_stateEvent_FetchInvX_SM =  registerStatistic<uint64_t>("stateEvent_FetchInvX_SM");
        stat_stateEvent_FetchInvX_E =   registerStatistic<uint64_t>("stateEvent_FetchInvX_E");
        stat_stateEvent_FetchInvX_M =   registerStatistic<uint64_t>("stateEvent_FetchInvX_M");
        stat_stateEvent_FetchInvX_EI =  registerStatistic<uint64_t>("stateEvent_FetchInvX_EI");
        stat_stateEvent_FetchInvX_MI =  registerStatistic<uint64_t>("stateEvent_FetchInvX_MI");
        stat_stateEvent_FetchInvX_EInv =    registerStatistic<uint64_t>("stateEvent_FetchInvX_EInv");
        stat_stateEvent_FetchInvX_EInvX =   registerStatistic<uint64_t>("stateEvent_FetchInvX_EInvX");
        stat_stateEvent_FetchInvX_MInv =    registerStatistic<uint64_t>("stateEvent_FetchInvX_MInv");
        stat_stateEvent_FetchInvX_MInvX =   registerStatistic<uint64_t>("stateEvent_FetchInvX_MInvX");
        stat_stateEvent_FetchInvX_ED =  registerStatistic<uint64_t>("stateEvent_FetchInvX_ED");
        stat_stateEvent_FetchInvX_MD =  registerStatistic<uint64_t>("stateEvent_FetchInvX_MD");
        stat_stateEvent_Fetch_I =       registerStatistic<uint64_t>("stateEvent_Fetch_I");
        stat_stateEvent_Fetch_IS =      registerStatistic<uint64_t>("stateEvent_Fetch_IS");
        stat_stateEvent_Fetch_IM =      registerStatistic<uint64_t>("stateEvent_Fetch_IM");
        stat_stateEvent_Fetch_SM =      registerStatistic<uint64_t>("stateEvent_Fetch_SM");
        stat_stateEvent_Fetch_S =       registerStatistic<uint64_t>("stateEvent_Fetch_S");
        stat_stateEvent_Fetch_SInv =    registerStatistic<uint64_t>("stateEvent_Fetch_SInv");
        stat_stateEvent_Fetch_SI =      registerStatistic<uint64_t>("stateEvent_Fetch_SI");
        stat_stateEvent_Fetch_SD =      registerStatistic<uint64_t>("stateEvent_Fetch_SD");
        stat_stateEvent_FetchResp_I =   registerStatistic<uint64_t>("stateEvent_FetchResp_I");
        stat_stateEvent_FetchResp_SI = registerStatistic<uint64_t>("stateEvent_FetchResp_SI");
        stat_stateEvent_FetchResp_EI = registerStatistic<uint64_t>("stateEvent_FetchResp_EI");
        stat_stateEvent_FetchResp_MI = registerStatistic<uint64_t>("stateEvent_FetchResp_MI");
        stat_stateEvent_FetchResp_SInv = registerStatistic<uint64_t>("stateEvent_FetchResp_SInv");
        stat_stateEvent_FetchResp_SMInv = registerStatistic<uint64_t>("stateEvent_FetchResp_SMInv");
        stat_stateEvent_FetchResp_EInv = registerStatistic<uint64_t>("stateEvent_FetchResp_EInv");
        stat_stateEvent_FetchResp_MInv = registerStatistic<uint64_t>("stateEvent_FetchResp_MInv");
        stat_stateEvent_FetchResp_SD = registerStatistic<uint64_t>("stateEvent_FetchResp_SD");
        stat_stateEvent_FetchResp_SMD = registerStatistic<uint64_t>("stateEvent_FetchResp_SMD");
        stat_stateEvent_FetchResp_ED = registerStatistic<uint64_t>("stateEvent_FetchResp_ED");
        stat_stateEvent_FetchResp_MD = registerStatistic<uint64_t>("stateEvent_FetchResp_MD");
        stat_stateEvent_FetchXResp_I = registerStatistic<uint64_t>("stateEvent_FetchXResp_I");
        stat_stateEvent_FetchXResp_EInvX = registerStatistic<uint64_t>("stateEvent_FetchXResp_EInvX");
        stat_stateEvent_FetchXResp_MInvX = registerStatistic<uint64_t>("stateEvent_FetchXResp_MInvX");
        stat_stateEvent_AckInv_I = registerStatistic<uint64_t>("stateEvent_AckInv_I");
        stat_stateEvent_AckInv_SInv = registerStatistic<uint64_t>("stateEvent_AckInv_SInv");
        stat_stateEvent_AckInv_SMInv = registerStatistic<uint64_t>("stateEvent_AckInv_SMInv");
        stat_stateEvent_AckInv_SI = registerStatistic<uint64_t>("stateEvent_AckInv_SI");
        stat_stateEvent_AckInv_EI = registerStatistic<uint64_t>("stateEvent_AckInv_EI");
        stat_stateEvent_AckInv_MI = registerStatistic<uint64_t>("stateEvent_AckInv_MI");
        stat_stateEvent_AckInv_EInv = registerStatistic<uint64_t>("stateEvent_AckInv_EInv");
        stat_stateEvent_AckInv_MInv = registerStatistic<uint64_t>("stateEvent_AckInv_MInv");
        stat_stateEvent_AckPut_I = registerStatistic<uint64_t>("stateEvent_AckPut_I");
        
        stat_latency_GetS_IS =      registerStatistic<uint64_t>("latency_GetS_IS");
        stat_latency_GetS_M =       registerStatistic<uint64_t>("latency_GetS_M");
        stat_latency_GetX_IM =      registerStatistic<uint64_t>("latency_GetX_IM");
        stat_latency_GetX_SM =      registerStatistic<uint64_t>("latency_GetX_SM");
        stat_latency_GetX_M =       registerStatistic<uint64_t>("latency_GetX_M");
        stat_latency_GetSEx_IM =    registerStatistic<uint64_t>("latency_GetSEx_IM");
        stat_latency_GetSEx_SM =    registerStatistic<uint64_t>("latency_GetSEx_SM");
        stat_latency_GetSEx_M =     registerStatistic<uint64_t>("latency_GetSEx_M");

        stat_eventSent_GetS = registerStatistic<uint64_t>("eventSent_GetS");
        stat_eventSent_GetX = registerStatistic<uint64_t>("eventSent_GetX");
        stat_eventSent_GetSEx = registerStatistic<uint64_t>("eventSent_GetSEx");
        stat_eventSent_GetSResp = registerStatistic<uint64_t>("eventSent_GetSResp");
        stat_eventSent_GetXResp = registerStatistic<uint64_t>("eventSent_GetXResp");
        stat_eventSent_PutS = registerStatistic<uint64_t>("eventSent_PutS");
        stat_eventSent_PutE = registerStatistic<uint64_t>("eventSent_PutE");
        stat_eventSent_PutM = registerStatistic<uint64_t>("eventSent_PutM");
        stat_eventSent_Inv = registerStatistic<uint64_t>("eventSent_Inv");
        stat_eventSent_Fetch = registerStatistic<uint64_t>("eventSent_Fetch");
        stat_eventSent_FetchInv = registerStatistic<uint64_t>("eventSent_FetchInv");
        stat_eventSent_FetchInvX = registerStatistic<uint64_t>("eventSent_FetchInvX");
        stat_eventSent_FetchResp = registerStatistic<uint64_t>("eventSent_FetchResp");
        stat_eventSent_FetchXResp = registerStatistic<uint64_t>("eventSent_FetchXResp");
        stat_eventSent_AckInv = registerStatistic<uint64_t>("eventSent_AckInv");
        stat_eventSent_AckPut = registerStatistic<uint64_t>("eventSent_AckPut");
        stat_eventSent_NACK_up = registerStatistic<uint64_t>("eventSent_NACK_up");
        stat_eventSent_NACK_down = registerStatistic<uint64_t>("eventSent_NACK_down");
}



/**************************************/
/****** Functions to send events ******/
/**************************************/

/* Send a NACK in response to a request. Could be virtual if needed. */
void CoherenceController::sendNACK(MemEvent * event, bool up, SimTime_t timeInNano) {
    MemEvent *NACKevent = event->makeNACKResponse(event, timeInNano);
    
    uint64_t deliveryTime = timestamp_ + tagLatency_;
    Response resp = {NACKevent, deliveryTime};
        
    if (up) addToOutgoingQueueUp(resp);
    else addToOutgoingQueue(resp);

#ifdef __SST_DEBUG_OUTPUT__
        if (DEBUG_ALL || DEBUG_ADDR == event->getBaseAddr()) debug->debug(_L3_,"Sending NACK at cycle = %" PRIu64 "\n", deliveryTime);
#endif
}


/* Send response towards the CPU. L1s need to implement their own to split out the requested block */
uint64_t CoherenceController::sendResponseUp(MemEvent * event, State grantedState, vector<uint8_t>* data, bool replay, uint64_t baseTime, bool atomic) {
    MemEvent * responseEvent = event->makeResponse(grantedState);
    responseEvent->setDst(event->getSrc());
    responseEvent->setSize(event->getSize());
    if (data != NULL) responseEvent->setPayload(*data);
    
    if (baseTime < timestamp_) baseTime = timestamp_;
    uint64_t deliveryTime = baseTime + (replay ? mshrLatency_ : accessLatency_);
    Response resp = {responseEvent, deliveryTime};
    addToOutgoingQueueUp(resp);
    
#ifdef __SST_DEBUG_OUTPUT__
    if (DEBUG_ALL || DEBUG_ADDR == event->getBaseAddr()) debug->debug(_L3_,"Sending Response at cycle = %" PRIu64 ". Current Time = %" PRIu64 ", Addr = %" PRIx64 ", Dst = %s, Payload Bytes = %i, Granted State = %s\n", 
            deliveryTime, timestamp_, event->getAddr(), responseEvent->getDst().c_str(), responseEvent->getPayloadSize(), StateString[responseEvent->getGrantedState()]);
#endif

    return deliveryTime;
}
    

/* Resend an event that was NACKed
 * Add backoff latency to avoid too much traffic
 */
void CoherenceController::resendEvent(MemEvent * event, bool up) {
    // Calculate backoff    
    int retries = event->getRetries();
    if (retries > 10) retries = 10;
    uint64_t backoff = ( 0x1 << retries);
    event->incrementRetries();

    uint64_t deliveryTime =  timestamp_ + mshrLatency_ + backoff;
    Response resp = {event, deliveryTime};
    if (!up) addToOutgoingQueue(resp);
    else addToOutgoingQueueUp(resp);

#ifdef __SST_DEBUG_OUTPUT__
    if (DEBUG_ALL || DEBUG_ADDR == event->getBaseAddr()) debug->debug(_L3_,"Sending request: Addr = %" PRIx64 ", BaseAddr = %" PRIx64 ", Cmd = %s\n", 
            event->getAddr(), event->getBaseAddr(), CommandString[event->getCmd()]);
#endif
}
  

/* Forward a message to a lower level (towards memory) in the hierarchy */
uint64_t CoherenceController::forwardMessage(MemEvent * event, Addr baseAddr, unsigned int requestSize, uint64_t baseTime, vector<uint8_t>* data) {
    /* Create event to be forwarded */
    MemEvent* forwardEvent;
    forwardEvent = new MemEvent(*event);
    forwardEvent->setSrc(parent->getName());
    forwardEvent->setDst(getDestination(baseAddr));
    forwardEvent->setSize(requestSize);
    
    if (data != NULL) forwardEvent->setPayload(*data);

    /* Determine latency in cycles */
    uint64_t deliveryTime;
    if (baseTime < timestamp_) baseTime = timestamp_;
    if (event->queryFlag(MemEvent::F_NONCACHEABLE)) {
        forwardEvent->setFlag(MemEvent::F_NONCACHEABLE);
        deliveryTime = timestamp_ + mshrLatency_;
    } else deliveryTime = baseTime + tagLatency_; 
    
    Response fwdReq = {forwardEvent, deliveryTime};
    addToOutgoingQueue(fwdReq);

#ifdef __SST_DEBUG_OUTPUT__
    if (DEBUG_ALL || DEBUG_ADDR == event->getBaseAddr()) debug->debug(_L3_,"Forwarding request at cycle = %" PRIu64 "\n", deliveryTime);        
#endif
    return deliveryTime;
}
    


/**************************************/
/******* Manage outgoing events *******/
/**************************************/


/* Send outgoing commands to port manager */
bool CoherenceController::sendOutgoingCommands(SimTime_t curTime) {
    // Update timestamp
    timestamp_++;

    // Check for ready events in outgoing 'down' queue
    while (!outgoingEventQueue_.empty() && outgoingEventQueue_.front().deliveryTime <= timestamp_) {
        MemEvent *outgoingEvent = outgoingEventQueue_.front().event;
        portMgr_->sendTowardsMem(outgoingEvent);
        recordEventSentDown(outgoingEvent->getCmd());
        outgoingEventQueue_.pop_front();

#ifdef __SST_DEBUG_OUTPUT__
        if (DEBUG_ALL || outgoingEvent->getBaseAddr() == DEBUG_ADDR) {
            debug->debug(_L4_,"SEND. Cmd: %s, BsAddr: %" PRIx64 ", Addr: %" PRIx64 ", Rqstr: %s, Src: %s, Dst: %s, PreF:%s, Rqst size = %u, Payload size = %u, time: (%" PRIu64 ", %" PRIu64 ")\n",
                    CommandString[outgoingEvent->getCmd()], outgoingEvent->getBaseAddr(), outgoingEvent->getAddr(), outgoingEvent->getRqstr().c_str(), outgoingEvent->getSrc().c_str(), 
                    outgoingEvent->getDst().c_str(), outgoingEvent->isPrefetch() ? "true" : "false", outgoingEvent->getSize(), outgoingEvent->getPayloadSize(), timestamp_, curTime);
        }
#endif
    }

    // Check for ready events in outgoing 'up' queue
    while (!outgoingEventQueueUp_.empty() && outgoingEventQueueUp_.front().deliveryTime <= timestamp_) {
        MemEvent * outgoingEvent = outgoingEventQueueUp_.front().event;
        portMgr_->sendTowardsCPU(outgoingEvent);
        recordEventSentUp(outgoingEvent->getCmd());
        outgoingEventQueueUp_.pop_front();

#ifdef __SST_DEBUG_OUTPUT__
        if (DEBUG_ALL || outgoingEvent->getBaseAddr() == DEBUG_ADDR) {
            debug->debug(_L4_,"SEND. Cmd: %s, BsAddr: %" PRIx64 ", Addr: %" PRIx64 ", Rqstr: %s, Src: %s, Dst: %s, PreF:%s, Rqst size = %u, Payload size = %u, time: (%" PRIu64 ", %" PRIu64 ")\n",
                    CommandString[outgoingEvent->getCmd()], outgoingEvent->getBaseAddr(), outgoingEvent->getAddr(), outgoingEvent->getRqstr().c_str(), outgoingEvent->getSrc().c_str(), 
                    outgoingEvent->getDst().c_str(), outgoingEvent->isPrefetch() ? "true" : "false", outgoingEvent->getSize(), outgoingEvent->getPayloadSize(), timestamp_, curTime);
        }
#endif
    }

    // Return whether it's ok for the cache to turn off the clock - we need it on to be able to send waiting events
    return outgoingEventQueue_.empty() && outgoingEventQueueUp_.empty();
}


/* Add a new event to the outgoing queue down (towards memory)
 * Add in timestamp order but do not re-order for events to the same address
 * Cache lines/banks mostly take care of this, except when we invalidate
 * a block and then re-request it, the requests can get inverted.
 */
void CoherenceController::addToOutgoingQueue(Response& resp) {
    list<Response>::reverse_iterator rit;
    for (rit = outgoingEventQueue_.rbegin(); rit!= outgoingEventQueue_.rend(); rit++) {
        if (resp.deliveryTime >= (*rit).deliveryTime) break;
        if (resp.event->getBaseAddr() == (*rit).event->getBaseAddr()) break;
    }
    outgoingEventQueue_.insert(rit.base(), resp);
}

/* Add a new event to the outgoing queue up (towards memory)
 * Again, to do not reorder events to the same address
 */
void CoherenceController::addToOutgoingQueueUp(Response& resp) {
    list<Response>::reverse_iterator rit;
    for (rit = outgoingEventQueueUp_.rbegin(); rit != outgoingEventQueueUp_.rend(); rit++) {
        if (resp.deliveryTime >= (*rit).deliveryTime) break;
        if (resp.event->getBaseAddr() == (*rit).event->getBaseAddr()) break;
    }
    outgoingEventQueueUp_.insert(rit.base(), resp);
}



/**************************************/
/************ Miscellaneous ***********/
/**************************************/

/* Call back to listener */
void CoherenceController::notifyListenerOfAccess(MemEvent * event, NotifyAccessType accessT, NotifyResultType resultT) {
    if (!event->isPrefetch()) {
        CacheListenerNotification notify(event->getBaseAddr(), event->getVirtualAddress(),
                event->getInstructionPointer(), event->getSize(), accessT, resultT);
        listener_->notifyAccess(notify);
    }
}

/* For sliced/distributed caches, return the home cache for a given address */    
std::string CoherenceController::getDestination(Addr baseAddr) {
    if (lowerLevelCacheNames_.size() == 1) {
        return lowerLevelCacheNames_.front();
    } else if (lowerLevelCacheNames_.size() > 1) {
        // round robin for now
        int index = (baseAddr/lineSize_) % lowerLevelCacheNames_.size();
        return lowerLevelCacheNames_[index];
    } else {
        return "";
    }
}

    

/**************************************/
/******** Statistics handling *********/
/**************************************/

/* Record latency TODO should probably move to port manager */
void CoherenceController::recordLatency(Command cmd, State state, uint64_t latency) {
    switch (state) {
        case IS:
            stat_latency_GetS_IS->addData(latency);
            break;
        case IM:
            if (cmd == GetX) stat_latency_GetX_IM->addData(latency);
            else stat_latency_GetSEx_IM->addData(latency);
            break;
        case SM:
            if (cmd == GetX) stat_latency_GetX_SM->addData(latency);
            else stat_latency_GetSEx_SM->addData(latency);
            break;
        case M:
            if (cmd == GetS) stat_latency_GetS_M->addData(latency);
            if (cmd == GetX) stat_latency_GetX_M->addData(latency);
            else stat_latency_GetSEx_M->addData(latency);
            break;
        default:
            break;
    }
}


/* Record the number of times an event arrived in a given state */
void CoherenceController::recordStateEventCount(Command cmd, State state) {
    switch (cmd) {
        case GetS:
            if (state == I) stat_stateEvent_GetS_I->addData(1);
            else if (state == S) stat_stateEvent_GetS_S->addData(1);
            else if (state == E) stat_stateEvent_GetS_E->addData(1);
            else if (state == M) stat_stateEvent_GetS_M->addData(1);
            break;
        case GetX:
            if (state == I) stat_stateEvent_GetX_I->addData(1);
            else if (state == S) stat_stateEvent_GetX_S->addData(1);
            else if (state == E) stat_stateEvent_GetX_E->addData(1);
            else if (state == M) stat_stateEvent_GetX_M->addData(1);
            break;
        case GetSEx:
            if (state == I) stat_stateEvent_GetSEx_I->addData(1);
            else if (state == S) stat_stateEvent_GetSEx_S->addData(1);
            else if (state == E) stat_stateEvent_GetSEx_E->addData(1);
            else if (state == M) stat_stateEvent_GetSEx_M->addData(1);
            break;
        case GetSResp:
            if (state == IS) stat_stateEvent_GetSResp_IS->addData(1);
            else if (state == IM) stat_stateEvent_GetSResp_IM->addData(1);
            else if (state == SM) stat_stateEvent_GetSResp_SM->addData(1);
            else if (state == SM_Inv) stat_stateEvent_GetSResp_SMInv->addData(1);
            break;
        case GetXResp:
            if (state == IM) stat_stateEvent_GetXResp_IM->addData(1);
            else if (state == SM) stat_stateEvent_GetXResp_SM->addData(1);
            else if (state == SM_Inv) stat_stateEvent_GetXResp_SMInv->addData(1);
            break;
        case PutS:
            if (state == I) stat_stateEvent_PutS_I->addData(1);
            else if (state == S) stat_stateEvent_PutS_S->addData(1);
            else if (state == E) stat_stateEvent_PutS_E->addData(1);
            else if (state == M) stat_stateEvent_PutS_M->addData(1);
            else if (state == S_D) stat_stateEvent_PutS_SD->addData(1);
            else if (state == E_D) stat_stateEvent_PutS_ED->addData(1);
            else if (state == M_D) stat_stateEvent_PutS_MD->addData(1);
            else if (state == SM_D) stat_stateEvent_PutS_SMD->addData(1);
            else if (state == S_Inv) stat_stateEvent_PutS_SInv->addData(1);
            else if (state == SI) stat_stateEvent_PutS_SI->addData(1);
            else if (state == EI) stat_stateEvent_PutS_EI->addData(1);
            else if (state == MI) stat_stateEvent_PutS_MI->addData(1);
            else if (state == E_Inv) stat_stateEvent_PutS_EInv->addData(1);
            else if (state == E_InvX) stat_stateEvent_PutS_EInvX->addData(1);
            else if (state == M_Inv) stat_stateEvent_PutS_MInv->addData(1);
            else if (state == SM_Inv) stat_stateEvent_PutS_SMInv->addData(1);
            break;
        case PutE:
            if (state == I) stat_stateEvent_PutE_I->addData(1);
            else if (state == E) stat_stateEvent_PutE_E->addData(1);
            else if (state == M) stat_stateEvent_PutE_M->addData(1);
            else if (state == EI) stat_stateEvent_PutE_EI->addData(1);
            else if (state == MI) stat_stateEvent_PutE_MI->addData(1);
            else if (state == E_Inv) stat_stateEvent_PutE_EInv->addData(1);
            else if (state == M_Inv) stat_stateEvent_PutE_MInv->addData(1);
            else if (state == E_InvX) stat_stateEvent_PutE_EInvX->addData(1);
            else if (state == M_InvX) stat_stateEvent_PutE_MInvX->addData(1);
            break;
        case PutM:
            if (state == I) stat_stateEvent_PutM_I->addData(1);
            else if (state == E) stat_stateEvent_PutM_E->addData(1);
            else if (state == M) stat_stateEvent_PutM_M->addData(1);
            else if (state == EI) stat_stateEvent_PutM_EI->addData(1);
            else if (state == MI) stat_stateEvent_PutM_MI->addData(1);
            else if (state == E_Inv) stat_stateEvent_PutM_EInv->addData(1);
            else if (state == M_Inv) stat_stateEvent_PutM_MInv->addData(1);
            else if (state == E_InvX) stat_stateEvent_PutM_EInvX->addData(1);
            else if (state == M_InvX) stat_stateEvent_PutM_MInvX->addData(1);
            break;
        case Inv:
            if (state == I) stat_stateEvent_Inv_I->addData(1);
            else if (state == IS) stat_stateEvent_Inv_IS->addData(1);
            else if (state == IM) stat_stateEvent_Inv_IM->addData(1);
            else if (state == S) stat_stateEvent_Inv_S->addData(1);
            else if (state == SM) stat_stateEvent_Inv_SM->addData(1);
            else if (state == S_Inv) stat_stateEvent_Inv_SInv->addData(1);
            else if (state == SI) stat_stateEvent_Inv_SI->addData(1);
            else if (state == SM_Inv) stat_stateEvent_Inv_SMInv->addData(1);
            else if (state == S_D) stat_stateEvent_Inv_SD->addData(1);
            break;
        case FetchInv:
            if (state == I) stat_stateEvent_FetchInv_I->addData(1);
            else if (state == IS) stat_stateEvent_FetchInv_IS->addData(1);
            else if (state == IM) stat_stateEvent_FetchInv_IM->addData(1);
            else if (state == SM) stat_stateEvent_FetchInv_SM->addData(1);
            else if (state == S) stat_stateEvent_FetchInv_S->addData(1);
            else if (state == E) stat_stateEvent_FetchInv_E->addData(1);
            else if (state == M) stat_stateEvent_FetchInv_M->addData(1);
            else if (state == EI) stat_stateEvent_FetchInv_EI->addData(1);
            else if (state == MI) stat_stateEvent_FetchInv_MI->addData(1);
            else if (state == E_Inv) stat_stateEvent_FetchInv_EInv->addData(1);
            else if (state == E_InvX) stat_stateEvent_FetchInv_EInvX->addData(1);
            else if (state == M_Inv) stat_stateEvent_FetchInv_MInv->addData(1);
            else if (state == M_InvX) stat_stateEvent_FetchInv_MInvX->addData(1);
            else if (state == S_D) stat_stateEvent_FetchInv_SD->addData(1);
            else if (state == E_D) stat_stateEvent_FetchInv_ED->addData(1);
            else if (state == M_D) stat_stateEvent_FetchInv_MD->addData(1);
            break;
        case FetchInvX:
            if (state == I) stat_stateEvent_FetchInvX_I->addData(1);
            else if (state == IS) stat_stateEvent_FetchInvX_IS->addData(1);
            else if (state == IM) stat_stateEvent_FetchInvX_IM->addData(1);
            else if (state == SM) stat_stateEvent_FetchInvX_SM->addData(1);
            else if (state == E) stat_stateEvent_FetchInvX_E->addData(1);
            else if (state == M) stat_stateEvent_FetchInvX_M->addData(1);
            else if (state == EI) stat_stateEvent_FetchInvX_EI->addData(1);
            else if (state == MI) stat_stateEvent_FetchInvX_MI->addData(1);
            else if (state == E_Inv) stat_stateEvent_FetchInvX_EInv->addData(1);
            else if (state == E_InvX) stat_stateEvent_FetchInvX_EInvX->addData(1);
            else if (state == M_Inv) stat_stateEvent_FetchInvX_MInv->addData(1);
            else if (state == M_InvX) stat_stateEvent_FetchInvX_MInvX->addData(1);
            else if (state == E_D) stat_stateEvent_FetchInvX_ED->addData(1);
            else if (state == M_D) stat_stateEvent_FetchInvX_MD->addData(1);
            break;
        case Fetch:
            if (state == I) stat_stateEvent_Fetch_I->addData(1);
            else if (state == IS) stat_stateEvent_Fetch_IS->addData(1);
            else if (state == IM) stat_stateEvent_Fetch_IM->addData(1);
            else if (state == S) stat_stateEvent_Fetch_S->addData(1);
            else if (state == SM) stat_stateEvent_Fetch_SM->addData(1);
            else if (state == S_Inv) stat_stateEvent_Fetch_SInv->addData(1);
            else if (state == SI) stat_stateEvent_Fetch_SI->addData(1);
            else if (state == S_D) stat_stateEvent_Fetch_SD->addData(1);
            break;
        case FetchResp:
            if (state == I) stat_stateEvent_FetchResp_I->addData(1);
            else if (state == EI) stat_stateEvent_FetchResp_SI->addData(1);
            else if (state == EI) stat_stateEvent_FetchResp_EI->addData(1);
            else if (state == MI) stat_stateEvent_FetchResp_MI->addData(1);
            else if (state == S_Inv) stat_stateEvent_FetchResp_SInv->addData(1);
            else if (state == SM_Inv) stat_stateEvent_FetchResp_SMInv->addData(1);
            else if (state == E_Inv) stat_stateEvent_FetchResp_EInv->addData(1);
            else if (state == M_Inv) stat_stateEvent_FetchResp_MInv->addData(1);
            else if (state == S_D) stat_stateEvent_FetchResp_SD->addData(1);
            else if (state == SM_D) stat_stateEvent_FetchResp_SMD->addData(1);
            else if (state == E_D) stat_stateEvent_FetchResp_ED->addData(1);
            else if (state == M_D) stat_stateEvent_FetchResp_MD->addData(1);
            break;
        case FetchXResp:
            if (state == I) stat_stateEvent_FetchXResp_I->addData(1);
            else if (state == E_InvX) stat_stateEvent_FetchXResp_EInvX->addData(1);
            else if (state == M_InvX) stat_stateEvent_FetchXResp_MInvX->addData(1);
            break;
        case AckInv:
            if (state == I) stat_stateEvent_AckInv_I->addData(1);
            else if (state == SI) stat_stateEvent_AckInv_SI->addData(1);
            else if (state == EI) stat_stateEvent_AckInv_EI->addData(1);
            else if (state == MI) stat_stateEvent_AckInv_MI->addData(1);
            else if (state == S_Inv) stat_stateEvent_AckInv_SInv->addData(1);
            else if (state == E_Inv) stat_stateEvent_AckInv_EInv->addData(1);
            else if (state == M_Inv) stat_stateEvent_AckInv_MInv->addData(1);
            else if (state == SM_Inv) stat_stateEvent_AckInv_SMInv->addData(1);
            break;
        case AckPut:
            if (state == I) stat_stateEvent_AckPut_I->addData(1);
            break;
        default:
            break;
    } 
}

/* Record the state a block was in when an eviction on it was attempted */
void CoherenceController::recordEvictionState(State state) {
        switch (state) {
            case I:
                stat_evict_I->addData(1);
                break;
            case E:
                stat_evict_E->addData(1);
                break;
            case M:
                stat_evict_M->addData(1);
                break;
            case IS:
                stat_evict_IS->addData(1);
                break;
            case IM:
                stat_evict_IM->addData(1);
                break;
            case I_B:
                stat_evict_IB->addData(1);
                break;
            case S_B:
                stat_evict_SB->addData(1);
            default:
                break;
        }

    }

/* Record how many times each event type was sent up */
void CoherenceController::recordEventSentUp(Command cmd) {
    switch (cmd) {
        case GetSResp:
            stat_eventSent_GetSResp->addData(1);
            break;
        case GetXResp:
            stat_eventSent_GetXResp->addData(1);
            break;
        case Inv:
            stat_eventSent_Inv->addData(1);
            break;
        case Fetch:
            stat_eventSent_Fetch->addData(1);
            break;
            case FetchInv:
                stat_eventSent_FetchInv->addData(1);
                break;
            case FetchInvX:
                stat_eventSent_FetchInvX->addData(1);
                break;
            case AckPut:
                stat_eventSent_AckPut->addData(1);
                break;
            case NACK:
                stat_eventSent_NACK_up->addData(1);
                break;
            default: 
                break;
        }
    }

/* Record how many times each event type was sent down */
void CoherenceController::recordEventSentDown(Command cmd) {
    switch (cmd) {
        case GetS:
            stat_eventSent_GetS->addData(1);
            break;
        case GetX:
            stat_eventSent_GetX->addData(1);
            break;
        case GetSEx:
            stat_eventSent_GetSEx->addData(1);
            break;
        case PutS:
            stat_eventSent_PutS->addData(1);
            break;
        case PutE:
                stat_eventSent_PutE->addData(1);
                break;
            case PutM:
                stat_eventSent_PutM->addData(1);
                break;
            case FetchResp:
                stat_eventSent_FetchResp->addData(1);
                break;
            case FetchXResp:
                stat_eventSent_FetchXResp->addData(1);
                break;
            case AckInv:
                stat_eventSent_AckInv->addData(1);
                break;
            case NACK:
                stat_eventSent_NACK_down->addData(1);
                break;
            default: break;
        }
    }




/**************************************/
/******** Setup related tasks *********/
/**************************************/


/* Setup variables controlling interactions with other memory levels */
void CoherenceController::setupLowerStatus(bool isLastCoherenceLevel, bool lowerIsNoninclusive, bool lowerIsDirectory) {
    silentEvictClean_       = isLastCoherenceLevel; // Silently evict clean blocks if there's just a memory below us
    expectWritebackAck_     = !isLastCoherenceLevel && (lowerIsDirectory || lowerIsNoninclusive);  // Expect writeback ack if there's a dir below us or a non-inclusive cache
    writebackCleanBlocks_   = lowerIsNoninclusive;  // Writeback clean data if lower is non-inclusive - otherwise control message only
        
    if (lowerLevelCacheNames_.empty()) lowerLevelCacheNames_.push_back(""); // Avoid segfault on access
    if (upperLevelCacheNames_.empty()) upperLevelCacheNames_.push_back(""); // Avoid segfault on access
}


   
