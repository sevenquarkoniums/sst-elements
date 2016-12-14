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

#ifndef L1INCOHERENTCONTROLLER_H
#define L1INCOHERENTCONTROLLER_H

#include <iostream>
#include "coherenceController.h"


namespace SST { namespace MemHierarchy {

class L1IncoherentController : public CoherenceController {
public:
    /** Constructor for L1IncoherentController */
    L1IncoherentController(Component* comp, Params& params) : CoherenceController(comp, params) {
        debug->debug(_INFO_,"--------------------------- Initializing [L1Controller] ... \n\n");
       
        /* Register statistics */
        stat_stateEvent_GetS_I = registerStatistic<uint64_t>("stateEvent_GetS_I");
        stat_stateEvent_GetS_E = registerStatistic<uint64_t>("stateEvent_GetS_E");
        stat_stateEvent_GetS_M = registerStatistic<uint64_t>("stateEvent_GetS_M");
        stat_stateEvent_GetX_I = registerStatistic<uint64_t>("stateEvent_GetX_I");
        stat_stateEvent_GetX_E = registerStatistic<uint64_t>("stateEvent_GetX_E");
        stat_stateEvent_GetX_M = registerStatistic<uint64_t>("stateEvent_GetX_M");
        stat_stateEvent_GetSEx_I = registerStatistic<uint64_t>("stateEvent_GetSEx_I");
        stat_stateEvent_GetSEx_E = registerStatistic<uint64_t>("stateEvent_GetSEx_E");
        stat_stateEvent_GetSEx_M = registerStatistic<uint64_t>("stateEvent_GetSEx_M");
        stat_stateEvent_GetSResp_IS = registerStatistic<uint64_t>("stateEvent_GetXResp_IS");
        stat_stateEvent_GetXResp_IM = registerStatistic<uint64_t>("stateEvent_GetXResp_IM");
        stat_stateEvent_FlushLine_I = registerStatistic<uint64_t>("stateEvent_FlushLine_I");
        stat_stateEvent_FlushLine_E = registerStatistic<uint64_t>("stateEvent_FlushLine_E");
        stat_stateEvent_FlushLine_M = registerStatistic<uint64_t>("stateEvent_FlushLine_M");
        stat_stateEvent_FlushLine_IS = registerStatistic<uint64_t>("stateEvent_FlushLine_IS");
        stat_stateEvent_FlushLine_IM = registerStatistic<uint64_t>("stateEvent_FlushLine_IM");
        stat_stateEvent_FlushLine_IB = registerStatistic<uint64_t>("stateEvent_FlushLine_IB");
        stat_stateEvent_FlushLine_SB = registerStatistic<uint64_t>("stateEvent_FlushLine_SB");
        stat_stateEvent_FlushLineInv_I = registerStatistic<uint64_t>("stateEvent_FlushLineInv_I");
        stat_stateEvent_FlushLineInv_E = registerStatistic<uint64_t>("stateEvent_FlushLineInv_E");
        stat_stateEvent_FlushLineInv_M = registerStatistic<uint64_t>("stateEvent_FlushLineInv_M");
        stat_stateEvent_FlushLineInv_IS = registerStatistic<uint64_t>("stateEvent_FlushLineInv_IS");
        stat_stateEvent_FlushLineInv_IM = registerStatistic<uint64_t>("stateEvent_FlushLineInv_IM");
        stat_stateEvent_FlushLineInv_IB = registerStatistic<uint64_t>("stateEvent_FlushLineInv_IB");
        stat_stateEvent_FlushLineInv_SB = registerStatistic<uint64_t>("stateEvent_FlushLineInv_SB");
        stat_stateEvent_FlushLineResp_I = registerStatistic<uint64_t>("stateEvent_FlushLineResp_I");
        stat_stateEvent_FlushLineResp_IB = registerStatistic<uint64_t>("stateEvent_FlushLineResp_IB");
        stat_stateEvent_FlushLineResp_SB = registerStatistic<uint64_t>("stateEvent_FlushLineResp_SB");
    }

    ~L1IncoherentController() {}
    
    
    /** Used to determine in advance if an event will be a miss (and which kind of miss)
     * Used for statistics only
     */
    int isCoherenceMiss(MemEvent* event, CacheLine* cacheLine);
    
    /* Event handlers called by cache controller */
    /** Send cache line data to the lower level caches */
    CacheAction handleEviction(CacheLine* wbCacheLine, string origRqstr, bool ignoredParam=false);

    /** Process new cache request:  GetX, GetS, GetSEx */
    CacheAction handleRequest(MemEvent* event, CacheLine* cacheLine, bool replay);
   
    /** Process replacement - implemented for compatibility with CoherenceController but L1s do not receive replacements */
    CacheAction handleReplacement(MemEvent* event, CacheLine* cacheLine, MemEvent * reqEvent, bool replay);
    
    /** Process Inv */
    CacheAction handleInvalidationRequest(MemEvent *event, CacheLine* cacheLine, MemEvent * collisionEvent, bool replay);

    /** Process responses */
    CacheAction handleResponse(MemEvent* responseEvent, CacheLine* cacheLine, MemEvent* origRequest);

    /* Methods for sending events, called by cache controller */
    /** Send response up (to processor) */
    uint64_t sendResponseUp(MemEvent * event, State grantedState, vector<uint8_t>* data, bool replay, uint64_t baseTime, bool atomic = false);
    
/* Miscellaneous */
    /** Determine whether a NACKed event should be retried */
    bool isRetryNeeded(MemEvent * event, CacheLine * cacheLine);


    void printData(vector<uint8_t> * data, bool set);

private:
    /* Statistics */
    Statistic<uint64_t>* stat_stateEvent_GetS_I;
    Statistic<uint64_t>* stat_stateEvent_GetS_E;
    Statistic<uint64_t>* stat_stateEvent_GetS_M;
    Statistic<uint64_t>* stat_stateEvent_GetX_I;
    Statistic<uint64_t>* stat_stateEvent_GetX_E;
    Statistic<uint64_t>* stat_stateEvent_GetX_M;
    Statistic<uint64_t>* stat_stateEvent_GetSEx_I;
    Statistic<uint64_t>* stat_stateEvent_GetSEx_E;
    Statistic<uint64_t>* stat_stateEvent_GetSEx_M;
    Statistic<uint64_t>* stat_stateEvent_GetSResp_IS;
    Statistic<uint64_t>* stat_stateEvent_GetXResp_IM;
    Statistic<uint64_t>* stat_stateEvent_FlushLine_I;
    Statistic<uint64_t>* stat_stateEvent_FlushLine_E;
    Statistic<uint64_t>* stat_stateEvent_FlushLine_M;
    Statistic<uint64_t>* stat_stateEvent_FlushLine_IS;
    Statistic<uint64_t>* stat_stateEvent_FlushLine_IM;
    Statistic<uint64_t>* stat_stateEvent_FlushLine_IB;
    Statistic<uint64_t>* stat_stateEvent_FlushLine_SB;
    Statistic<uint64_t>* stat_stateEvent_FlushLineInv_I;
    Statistic<uint64_t>* stat_stateEvent_FlushLineInv_E;
    Statistic<uint64_t>* stat_stateEvent_FlushLineInv_M;
    Statistic<uint64_t>* stat_stateEvent_FlushLineInv_IS;
    Statistic<uint64_t>* stat_stateEvent_FlushLineInv_IM;
    Statistic<uint64_t>* stat_stateEvent_FlushLineInv_IB;
    Statistic<uint64_t>* stat_stateEvent_FlushLineInv_SB;
    Statistic<uint64_t>* stat_stateEvent_FlushLineResp_I;
    Statistic<uint64_t>* stat_stateEvent_FlushLineResp_IB;
    Statistic<uint64_t>* stat_stateEvent_FlushLineResp_SB;
    
    /* Private event handlers */
    /** Handle GetX request. Request upgrade if needed */
    CacheAction handleGetXRequest(MemEvent* event, CacheLine* cacheLine, bool replay);
    
    /** Handle GetS request. Request block if needed */
    CacheAction handleGetSRequest(MemEvent* event, CacheLine* cacheLine, bool replay);
    
    /** Handle FlushLine request. */
    CacheAction handleFlushLineRequest(MemEvent *event, CacheLine* cacheLine, MemEvent* reqEvent, bool replay);
    
    /** Handle FlushLineInv request */
    CacheAction handleFlushLineInvRequest(MemEvent *event, CacheLine* cacheLine, MemEvent* reqEvent, bool replay);

    /** Handle data response - GetSResp or GetXResp */
    void handleDataResponse(MemEvent* responseEvent, CacheLine * cacheLine, MemEvent * reqEvent);

    
    /* Methods for sending events */
    /** Send writeback request to lower level caches */
    void sendWriteback(Command cmd, CacheLine* cacheLine, string origRqstr);

    /** Forward a flush line request, with or without data */
    void forwardFlushLine(Addr baseAddr, Command cmd, string origRqstr, CacheLine * cacheLine);
    
    /** Send response to a flush request */
    void sendFlushResponse(MemEvent * requestEvent, bool success, uint64_t baseTime, bool replay);
};


}}


#endif

