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

#ifndef COHERENCECONTROLLER_H
#define COHERENCECONTROLLER_H

#include <sst_config.h>
#include <sst/core/subcomponent.h>

#include "portManager.h"
#include "util.h"
#include "cacheListener.h"
#include "cacheArray.h"
#include "mshr.h"

namespace SST { namespace MemHierarchy {
using namespace std;

class CoherenceController : public SST::SubComponent {

public:
    typedef CacheArray::CacheLine CacheLine;

    /***** Constructor & destructor *****/
    CoherenceController(Component * comp, Params &params);
    ~CoherenceController() {}

    /* Return whether a line access will be a miss and what kind (encoded in the int retval) */
    virtual int isCoherenceMiss(MemEvent * event, CacheLine * line) =0;

    /* Handle a cache request - GetS, GetX, etc. */
    virtual CacheAction handleRequest(MemEvent * event, CacheLine * line, bool replay) =0;

    /* Handle a cache replacement - PutS, PutM, etc. */
    virtual CacheAction handleReplacement(MemEvent * event, CacheLine * line, MemEvent * reqEvent, bool replay) =0;

    /* Handle a cache invalidation - Inv, FetchInv, etc. */
    virtual CacheAction handleInvalidationRequest(MemEvent * event, CacheLine * line, MemEvent * collisionEvent, bool replay) =0;

    /* Handle an eviction */
    virtual CacheAction handleEviction(CacheLine * line, string rqstr, bool fromDataCache=false) =0;
    
    /* Handle a response - AckInv, GetSResp, etc. */
    virtual CacheAction handleResponse(MemEvent * event, CacheLine * line, MemEvent * request) =0;

    /* Determine whether an event needs to be retried after a NACK */
    virtual bool isRetryNeeded(MemEvent * event, CacheLine * line) =0;

    /* Update timestamp in lockstep with parent */
    void updateTimestamp(uint64_t newTS) { timestamp_ = newTS; }

    
    /***** Functions for sending events *****/

    /* Send a NACK event. Used by child classes and cache controller */
    void sendNACK(MemEvent * event, bool up, SimTime_t timeInNano);

    /* Resend an event after a NACK */
    void resendEvent(MemEvent * event, bool towardsCPU);

    /* Send a response event up (towards CPU). L1s need to implement their own to split out requested bytes. */
    virtual uint64_t sendResponseUp(MemEvent * event, State grantedState, vector<uint8_t>* data, bool replay, uint64_t baseTime, bool atomic=false);

    /* Forward a message to a lower memory level (towards memory) */
    uint64_t forwardMessage(MemEvent * event, Addr baseAddr, unsigned int requestSize, uint64_t baseTime, vector<uint8_t>* data);


    /***** Manage outgoing event queuest *****/
    
    /* Send commands when their timestamp expires. Return whether queue is empty or not. */
    virtual bool sendOutgoingCommands(SimTime_t curTime);


    /***** Setup and initialization functions *****/

    /* Add cache names to destination lookup tables */
    void addLowerLevelCacheName(std::string name) { lowerLevelCacheNames_.push_back(name); }
    void addUpperLevelCacheName(std::string name) { upperLevelCacheNames_.push_back(name); }

    /* Initialize variables that tell this coherence controller how to interact with the cache below it */
    void setupLowerStatus(bool isLastLevel, bool isNoninclusive, bool isDir);

    /* Setup pointers to other subcomponents/cache structures */
    void setPortManager(PortManager* ptr) { portMgr_ = ptr; }
    void setCacheListener(CacheListener* ptr) { listener_ = ptr; }
    void setMSHR(MSHR* ptr) { mshr_ = ptr; }

    /* Setup debug info (this is cache-wide) */
    void setDebug(bool debugAll, Addr debugAddr) {
        DEBUG_ALL = debugAll;
        DEBUG_ADDR = debugAddr;
    }

    /***** Statistics *****/
    virtual void recordLatency(Command cmd, State state, uint64_t latency);
    
protected:
    struct Response {
        MemEvent* event;
        uint64_t deliveryTime;
    };

    /* Pointers to other subcomponents and cache structures */
    CacheListener*  listener_;
    PortManager*    portMgr_;
    MSHR *          mshr_;              // Pointer to cache's MSHR, coherence controllers are responsible for managing writeback acks
   
    /* Latency and timing related parameters */
    uint64_t        timestamp_;         // Local timestamp (cycles)
    uint64_t        accessLatency_;     // Cache access latency
    uint64_t        tagLatency_;        // Cache tag access latency
    uint64_t        mshrLatency_;       // MSHR lookup latency

    /* Outgoing event queues - events are stalled here to account for access latencies */
    list<Response> outgoingEventQueue_;
    list<Response> outgoingEventQueueUp_;
    
    /* Debug control */
    bool        DEBUG_ALL;
    Addr        DEBUG_ADDR;

    /* Output */
    Output*     output;
    Output*     debug;

    /* Parameters controlling how this cache interacts with the one below it */
    bool            writebackCleanBlocks_;  // Writeback clean data as opposed to just a coherence msg
    bool            silentEvictClean_;      // Silently evict clean blocks (currently ok when just mem below us)
    bool            expectWritebackAck_;    // Whether we should expect a writeback ack

    /* General parameters and structures */
    unsigned int lineSize_;
    vector<string>  lowerLevelCacheNames_;
    vector<string>  upperLevelCacheNames_;

    /***** Functions used by child classes *****/

    /* Add a new event to the outgoing command queue towards memory */
    void addToOutgoingQueue(Response& resp);

    /* Add a new event to the outgoing command queue towards the CPU */
    void addToOutgoingQueueUp(Response& resp);

    /* Return the destination for a given address - for sliced/distributed caches */
    std::string getDestination(Addr baseAddr);
    
    /* Statistics */
    virtual void recordStateEventCount(Command cmd, State state);
    virtual void recordEvictionState(State state);
    virtual void recordEventSentUp(Command cmd);
    virtual void recordEventSentDown(Command cmd);

    /* Listener callback */
    virtual void notifyListenerOfAccess(MemEvent * event, NotifyAccessType accessT, NotifyResultType resultT);


    // Eviction statistics, count how many times we attempted to evict a block in a particular state
    Statistic<uint64_t>* stat_evict_I;
    Statistic<uint64_t>* stat_evict_E;
    Statistic<uint64_t>* stat_evict_M;
    Statistic<uint64_t>* stat_evict_IS;
    Statistic<uint64_t>* stat_evict_IM;
    Statistic<uint64_t>* stat_evict_IB;
    Statistic<uint64_t>* stat_evict_SB;

    // State/event combinations for Stats API TODO is there a cleaner way to enumerate & declare these?
    Statistic<uint64_t>* stat_stateEvent_GetS_I;
    Statistic<uint64_t>* stat_stateEvent_GetS_S;
    Statistic<uint64_t>* stat_stateEvent_GetS_E;
    Statistic<uint64_t>* stat_stateEvent_GetS_M;
    Statistic<uint64_t>* stat_stateEvent_GetX_I;
    Statistic<uint64_t>* stat_stateEvent_GetX_S;
    Statistic<uint64_t>* stat_stateEvent_GetX_E;
    Statistic<uint64_t>* stat_stateEvent_GetX_M;
    Statistic<uint64_t>* stat_stateEvent_GetSEx_I;
    Statistic<uint64_t>* stat_stateEvent_GetSEx_S;
    Statistic<uint64_t>* stat_stateEvent_GetSEx_E;
    Statistic<uint64_t>* stat_stateEvent_GetSEx_M;
    Statistic<uint64_t>* stat_stateEvent_GetSResp_IS;
    Statistic<uint64_t>* stat_stateEvent_GetSResp_IM;
    Statistic<uint64_t>* stat_stateEvent_GetSResp_SM;
    Statistic<uint64_t>* stat_stateEvent_GetSResp_SMInv;
    Statistic<uint64_t>* stat_stateEvent_GetXResp_IM;
    Statistic<uint64_t>* stat_stateEvent_GetXResp_SM;
    Statistic<uint64_t>* stat_stateEvent_GetXResp_SMInv;
    Statistic<uint64_t>* stat_stateEvent_PutS_I;
    Statistic<uint64_t>* stat_stateEvent_PutS_S;
    Statistic<uint64_t>* stat_stateEvent_PutS_E;
    Statistic<uint64_t>* stat_stateEvent_PutS_M;
    Statistic<uint64_t>* stat_stateEvent_PutS_SD;
    Statistic<uint64_t>* stat_stateEvent_PutS_ED;
    Statistic<uint64_t>* stat_stateEvent_PutS_MD;
    Statistic<uint64_t>* stat_stateEvent_PutS_SMD;
    Statistic<uint64_t>* stat_stateEvent_PutS_SInv;
    Statistic<uint64_t>* stat_stateEvent_PutS_SI;
    Statistic<uint64_t>* stat_stateEvent_PutS_EI;
    Statistic<uint64_t>* stat_stateEvent_PutS_MI;
    Statistic<uint64_t>* stat_stateEvent_PutS_EInvX;
    Statistic<uint64_t>* stat_stateEvent_PutS_EInv;
    Statistic<uint64_t>* stat_stateEvent_PutS_MInv;
    Statistic<uint64_t>* stat_stateEvent_PutS_SMInv;
    Statistic<uint64_t>* stat_stateEvent_PutE_I;
    Statistic<uint64_t>* stat_stateEvent_PutE_E;
    Statistic<uint64_t>* stat_stateEvent_PutE_M;
    Statistic<uint64_t>* stat_stateEvent_PutE_EI;
    Statistic<uint64_t>* stat_stateEvent_PutE_MI;
    Statistic<uint64_t>* stat_stateEvent_PutE_EInv;
    Statistic<uint64_t>* stat_stateEvent_PutE_EInvX;
    Statistic<uint64_t>* stat_stateEvent_PutE_MInv;
    Statistic<uint64_t>* stat_stateEvent_PutE_MInvX;
    Statistic<uint64_t>* stat_stateEvent_PutM_I;
    Statistic<uint64_t>* stat_stateEvent_PutM_E;
    Statistic<uint64_t>* stat_stateEvent_PutM_M;
    Statistic<uint64_t>* stat_stateEvent_PutM_EI;
    Statistic<uint64_t>* stat_stateEvent_PutM_MI;
    Statistic<uint64_t>* stat_stateEvent_PutM_EInv;
    Statistic<uint64_t>* stat_stateEvent_PutM_EInvX;
    Statistic<uint64_t>* stat_stateEvent_PutM_MInv;
    Statistic<uint64_t>* stat_stateEvent_PutM_MInvX;
    Statistic<uint64_t>* stat_stateEvent_Inv_I;
    Statistic<uint64_t>* stat_stateEvent_Inv_IS;
    Statistic<uint64_t>* stat_stateEvent_Inv_IM;
    Statistic<uint64_t>* stat_stateEvent_Inv_S;
    Statistic<uint64_t>* stat_stateEvent_Inv_SM;
    Statistic<uint64_t>* stat_stateEvent_Inv_SInv;
    Statistic<uint64_t>* stat_stateEvent_Inv_SI;
    Statistic<uint64_t>* stat_stateEvent_Inv_SMInv;
    Statistic<uint64_t>* stat_stateEvent_Inv_SD;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_I;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_IS;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_IM;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_SM;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_S;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_E;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_M;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_EI;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_MI;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_EInv;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_EInvX;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_MInv;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_MInvX;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_SD;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_ED;
    Statistic<uint64_t>* stat_stateEvent_FetchInv_MD;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_I;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_IS;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_IM;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_SM;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_E;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_M;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_EI;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_MI;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_EInv;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_EInvX;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_MInv;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_MInvX;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_ED;
    Statistic<uint64_t>* stat_stateEvent_FetchInvX_MD;
    Statistic<uint64_t>* stat_stateEvent_Fetch_I;
    Statistic<uint64_t>* stat_stateEvent_Fetch_IS;
    Statistic<uint64_t>* stat_stateEvent_Fetch_IM;
    Statistic<uint64_t>* stat_stateEvent_Fetch_SM;
    Statistic<uint64_t>* stat_stateEvent_Fetch_S;
    Statistic<uint64_t>* stat_stateEvent_Fetch_SInv;
    Statistic<uint64_t>* stat_stateEvent_Fetch_SI;
    Statistic<uint64_t>* stat_stateEvent_Fetch_SD;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_I;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_SI;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_EI;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_MI;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_SInv;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_SMInv;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_EInv;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_MInv;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_SD;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_SMD;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_ED;
    Statistic<uint64_t>* stat_stateEvent_FetchResp_MD;
    Statistic<uint64_t>* stat_stateEvent_FetchXResp_I;
    Statistic<uint64_t>* stat_stateEvent_FetchXResp_EInvX;
    Statistic<uint64_t>* stat_stateEvent_FetchXResp_MInvX;
    Statistic<uint64_t>* stat_stateEvent_AckInv_I;
    Statistic<uint64_t>* stat_stateEvent_AckInv_SInv;
    Statistic<uint64_t>* stat_stateEvent_AckInv_EInv;
    Statistic<uint64_t>* stat_stateEvent_AckInv_MInv;
    Statistic<uint64_t>* stat_stateEvent_AckInv_SMInv;
    Statistic<uint64_t>* stat_stateEvent_AckInv_SI;
    Statistic<uint64_t>* stat_stateEvent_AckInv_EI;
    Statistic<uint64_t>* stat_stateEvent_AckInv_MI;
    Statistic<uint64_t>* stat_stateEvent_AckPut_I;

    Statistic<uint64_t>* stat_latency_GetS_IS;
    Statistic<uint64_t>* stat_latency_GetS_M;
    Statistic<uint64_t>* stat_latency_GetX_IM;
    Statistic<uint64_t>* stat_latency_GetX_SM;
    Statistic<uint64_t>* stat_latency_GetX_M;
    Statistic<uint64_t>* stat_latency_GetSEx_IM;
    Statistic<uint64_t>* stat_latency_GetSEx_SM;
    Statistic<uint64_t>* stat_latency_GetSEx_M;     
   
    // Count events sent
    Statistic<uint64_t>* stat_eventSent_GetS;       // All
    Statistic<uint64_t>* stat_eventSent_GetX;       // All
    Statistic<uint64_t>* stat_eventSent_GetSEx;     // All
    Statistic<uint64_t>* stat_eventSent_GetSResp;   // All
    Statistic<uint64_t>* stat_eventSent_GetXResp;   // All
    Statistic<uint64_t>* stat_eventSent_PutS;       // All
    Statistic<uint64_t>* stat_eventSent_PutE;       // All
    Statistic<uint64_t>* stat_eventSent_PutM;       // All
    Statistic<uint64_t>* stat_eventSent_Inv;        // Non-L1
    Statistic<uint64_t>* stat_eventSent_Fetch;      
    Statistic<uint64_t>* stat_eventSent_FetchInv;   // Non-L1
    Statistic<uint64_t>* stat_eventSent_FetchInvX;  // Non-L1
    Statistic<uint64_t>* stat_eventSent_FetchResp;  // All
    Statistic<uint64_t>* stat_eventSent_FetchXResp; // All
    Statistic<uint64_t>* stat_eventSent_AckInv;     // All
    Statistic<uint64_t>* stat_eventSent_AckPut;     // Non-L1
    Statistic<uint64_t>* stat_eventSent_NACK_up;    // Non-L1
    Statistic<uint64_t>* stat_eventSent_NACK_down;  // All

};

}}

#endif	/* COHERENCECONTROLLER_H */
