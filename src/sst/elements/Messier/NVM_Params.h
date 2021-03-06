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

#ifndef _H_SST_NVM_PARAMS
#define _H_SST_NVM_PARAMS


#include <sst_config.h>
#include <sst/core/component.h>
#include <sst/core/timeConverter.h>
#include <sst/elements/memHierarchy/memEvent.h>
#include<map>
#include<list>
//#include "Messier.h"

// This class structure represents the NVM parameters

using namespace SST; //::MessierComponent;

namespace SST{ namespace MessierComponent{

//using namespace SST::MessierComponent;

class NVM_PARAMS
{ 
	public:

		// The size of the whole rank in KB
		long long int size;

		// The size of the write buffer in number of entries
		int write_buffer_size;	

		// This determines the number of maximum buffer requests inside the controller
		int max_requests;

		// The number of possible outstanding requests inside the internal controller (not that once writes are written to the write buffer, they are deleted)
		int max_outstanding;

		// For power budget (at any time, the controller enforces write_weight*num_current_writes + read_weight*num_current_reads less than or equal max_current_weight
		float max_current_weight;

		// This determines the relative power consumption of a PCM write operation
		float write_weight;

		// This determines the relative power consumption of a PCM read operation
		float read_weight;

		// The clock of the internal controller of the DIMM in GHz
		float clock; 

		// The clock of the internal PCM memory
		float memory_clock;

		// The clock of the IO bus, this typically should be similar to the internal controller clock
		float io_clock;

		// The time to send a command from the internal controller till buffered inside the NVM chips
		int tCMD;

		// This is the access latency of a column for an already activated row buffer
		int tCL;

		// This is the actual read latency of a row and installing it on the row buffer
		int tRCD;

		// The latency of writing a column. Note that we assume internal PCMs write it directly to the PCM cells and update the row buffer (in case it was row-buffer hit)
		int tCL_W;

		// The time needed for submitting a data burst on the bus
		int tBURST;

		// This determines the device width in bits
		int device_width;

		// num ranks
		int num_ranks;

		// This determines the number of devices on the DIMM Ranks (the DIMM bus width is num_devices X  device_width)
		int num_devices;

		// This determines the number of banks on each Rank
		int num_banks;

		// This determines the row buffer size	
		int row_buffer_size;

		// This indicates the threshold for starting the write buffer flushing
		int flush_th; 

	public:

		void operator = (const NVM_PARAMS &D ) { 
			size = D.size;  // in KB, which mean 8GB

			write_buffer_size = D.write_buffer_size;	

			max_outstanding = D.max_outstanding;

			max_current_weight = D.max_current_weight;;

			write_weight = D.write_weight;

			read_weight = D.read_weight;

			clock = D.clock; 

			memory_clock = D.clock;

			io_clock = D.io_clock;;

			tCMD = D.tCMD;

			tCL = D.tCL;

			tRCD = D.tRCD;

			tCL_W = D.tCL_W;

			tBURST = D.tBURST;

			device_width = D.device_width;

			num_ranks = D.num_ranks;

			num_devices = D.num_devices;
			num_banks = D.num_banks;
			row_buffer_size = D.row_buffer_size;
			flush_th = D.flush_th;
			max_requests = D.max_requests;

		}
};
}}

#endif
