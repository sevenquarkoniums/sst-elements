#!/usr/bin/env python
'''
print out a line from a simulation result file.

'''
import sys

messageSize = int(sys.argv[1])
traceMode = sys.argv[2]
traceNum = int(sys.argv[3])
if traceMode == 'corner':
    folder = 'hybrid'
elif traceMode == 'empty':
    folder = 'empty'

fi = open('%s/G17R4N4_uti75_alltoall_mesSize%d_mesIter2_%s_%d_dflyhybrid_topo_easy_adaptive_alpha1.00_expIter0/ember.out'
        % (folder, messageSize, traceMode, traceNum),'r')
for line in fi:
    if line.startswith('Job Finished:'):
        print(line)
        break
