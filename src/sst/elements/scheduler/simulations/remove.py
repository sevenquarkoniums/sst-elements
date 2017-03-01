#!/usr/bin/env python
'''
remove some simulation results files.
'''
import os

for messageSize in [10**x for x in range(6,9)]:
    os.system('rm -r hybrid/G17R4N4_uti75_alltoall_mesSize%d_mesIter2_corner_1_dflyhybrid_topo_easy_adaptive_alpha1.00_expIter0'
            % (messageSize) )

