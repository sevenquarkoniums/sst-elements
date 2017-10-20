#!/usr/bin/env python
from os import system

for allocation in ['simple', 'random', 'dflyrdr', 'dflyrdg', 'dflyrrn', 'dflyrrr', 'dflyslurm', 'dflyhybrid']:
    for application in ['stencil','alltoall']:#['halo2d','fft','stencil','bcast','halo3d26','alltoall']:# add fft.
        fname = 'submit_allocOrder_%s_%s.sh' % (allocation, application)
        with open(fname, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('module load anaconda\n')
            f.write('./read.py hybridAll %s %s\n' % (allocation, application))
        cmd = 'qsub -cwd -o submit_allocOrder_%s_%s.out -l mem_free=2G,s_vmem=2G,h_vmem=2G -j y %s' % (allocation, application, fname)
        system(cmd)
