// Copyright 2009-2016 Sandia Corporation. Under the terms
// of Contract DE-AC04-94AL85000 with Sandia Corporation, the U.S.
// Government retains certain rights in this software.
//
// Copyright (c) 2009-2016, Sandia Corporation
// All rights reserved.
//
// This file is part of the SST software package. For license
// information, see the LICENSE file in the top level directory of the
// distribution.
//

/* Author: Amro Awad
 * E-mail: aawad@sandia.gov
 */



#include <sst_config.h>
#include <string>
#include "Messier.h"


using namespace SST::Interfaces;
using namespace SST;
using namespace SST::MessierComponent;


#define MESSIER_VERBOSE(LEVEL, OUTPUT) if(verbosity >= (LEVEL)) OUTPUT

void Messier::parser(NVM_PARAMS * nvm, SST::Params& params)
{
	//nvm = new NVM_PARAMS();

	nvm->size = (uint32_t) params.find<uint32_t>("size", 8388608);  // in KB, which mean 8GB

	nvm->write_buffer_size = (uint32_t) params.find<uint32_t>("write_buffer_size", 128); ;	

	nvm->max_outstanding = (uint32_t) params.find<uint32_t>("max_outstanding", 16) ;

	nvm->max_current_weight = (uint32_t) params.find<uint32_t>("max_current_weight", 120); ;

	nvm->write_weight = (uint32_t) params.find<uint32_t>("write_weight", 15); ;

	nvm->read_weight = (uint32_t) params.find<uint32_t>("read_weight", 3) ;

	// Skipe it for now
	//	clock = D.clock; 

	//memory_clock = D.clock;

	//io_clock = D.io_clock;;


	nvm->tCMD = (uint32_t) params.find<uint32_t>("tCMD", 1); ;

	nvm->tCL = (uint32_t) params.find<uint32_t>("tCL", 70); ;

	nvm->tRCD = (uint32_t) params.find<uint32_t>("tRCD", 300) ;

	std::cout<<"The value of tRCD is "<<nvm->tRCD<<std::endl;

	nvm->tCL_W = (uint32_t) params.find<uint32_t>("tCL_W", 1000) ;

	nvm->tBURST = (uint32_t) params.find<uint32_t>("tBURST", 7); ;

	nvm->device_width = (uint32_t) params.find<uint32_t>("device_width", 8) ;

	nvm->num_ranks = (uint32_t) params.find<uint32_t>("num_ranks", 1); ;

	nvm->num_devices = (uint32_t) params.find<uint32_t>("num_devices", 8) ;
	nvm->num_banks = (uint32_t) params.find<uint32_t>("num_banks", 16);
	nvm->row_buffer_size = (uint32_t) params.find<uint32_t>("row_buffer_size", 8192) ;
	nvm->flush_th = (uint32_t) params.find<uint32_t>("flush_th", 50) ;
	nvm->max_requests = (uint32_t) params.find<uint32_t>("max_requests", 32);


}

// Here we do the initialization of the Samba units of the system, connecting them to the cores and instantiating TLB hierachy objects for each one

Messier::Messier(SST::ComponentId_t id, SST::Params& params): Component(id) {


	char* link_buffer = (char*) malloc(sizeof(char) * 256);

//	m_memChan = configureLink( "bus", "1 ns" );

	sprintf(link_buffer, "bus");



       //m_memChan = configureLink(link_buffer, "0ps", new Event::Handler<TLBhierarchy>(TLB[i], &TLBhierarchy::handleEvent_CPU));

	nvm_params = new NVM_PARAMS();

	// This converts the sst paramters into an object of NVM_PARAMS, used to instantiate NVM_DIMM
	parser(nvm_params, params);


	// Instantiating the NVM-DIMM with the provided parameters 
	DIMM = new NVM_DIMM(*nvm_params);

        m_memChan = configureLink(link_buffer, "1ns", new Event::Handler<NVM_DIMM>(DIMM, &NVM_DIMM::handleRequest));

	DIMM->setMemChannel(m_memChan);

	std::cout<<"After initialization "<<std::endl;

	std::string cpu_clock = params.find<std::string>("clock", "1GHz");
	registerClock( cpu_clock, new Clock::Handler<Messier>(this, &Messier::tick ) );

}



Messier::Messier() : Component(-1)
{
	// for serialization only
	// 
}



bool Messier::tick(SST::Cycle_t x)
{

	// We tick the MMU hierarchy of each core
//	for(uint32_t i = 0; i < core_count; ++i)
	DIMM->tick();

	return false;
}
