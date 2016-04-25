#! /usr/bin/env python

import sys,os
from subprocess import call
import CrossProduct
from CrossProduct import *
import hashlib
import binascii

config = "emberLoad_circ.py"

tests = []
networks = [] 

#net = { 'topo' : 'torus',
#        'args' : [ 
#                    [ '--shape', ['2','4x4x4','8x8x8','16x16x16'] ] 
#                 ]
#      }
#
#networks.append(net);

net = { 'topo' : 'fattree',
        'args' : [  
                    ['--shape',   ['6,6:6,6:12']],
                 ]
      }

networks.append(net);

test = { 'motif' : 'AllPingPong',
         'args'  : [ 
                        [ 'iterations'  , ['5']],
                        [ 'messageSize' , ['1','40000']] 
                   ] 
        }

tests.append( test )

test = { 'motif' : 'Allreduce',
         'args'  : [  
                        [ 'iterations'  , ['5']],
                        [ 'count' , ['1']] 
                   ] 
        }

tests.append( test )

test = { 'motif' : 'Barrier',
         'args'  : [  
                        [ 'iterations'  , ['5']]
                   ] 
        }

tests.append( test )

test = { 'motif' : 'PingPong',
         'args'  : [  
                        [ 'iterations'  , ['5']],
                        [ 'messageSize' , ['10000','40000','160000']] 
                   ] 
        }

tests.append( test )

test = { 'motif' : 'Reduce',
         'args'  : [  
                        [ 'iterations'  , ['5']],
                        [ 'count' , ['1']] 
                   ] 
        }

tests.append( test )

test = { 'motif' : 'Ring',
         'args'  : [  
                        [ 'iterations'  , ['5']],
                        [ 'messagesize' , ['10000','40000','160000']] 
                   ] 
        }

tests.append( test )

test = { 'motif' : 'Sweep3D',
         'args'  : [  
                        [ 'pex'  , ['24']],
                        [ 'pey'  , ['18']],
                        [ 'computetime' , ['200']]
                   ] 
        }

tests.append( test )


test = { 'motif' : 'NASLU',
         'args'  : [  
                        [ 'pex'  , ['24']],
                        [ 'pey'  , ['18']]
                   ] 
        }

tests.append( test )

test = { 'motif' : 'CMT3D',
         'args'  : [  
                        [ 'px'  , ['6']],
                        [ 'py'  , ['6']],
                        [ 'pz'  , ['12']],
                        [ 'nsComputeMean'  , ['200']],
                        [ 'nsComputeStddev'  , ['20']]
                   ] 
        }

tests.append( test )

test = { 'motif' : 'Halo3DSV',
         'args'  : [  
                        [ 'pex'  , ['6']],
                        [ 'pey'  , ['6']],
                        [ 'pez'  , ['12']]
                   ] 
        }

tests.append( test )

for network in networks :
    for test in tests :
        for x in CrossProduct( network['args'] ) :
            for y in CrossProduct( test['args'] ):
                for p in ({'', '--platform=optic --rtrArb=xbar_arb_lru_infx'}):
                    print "sst --model-options=\"--topo={0} {1} {5} --netInspect=\"merlin.circuit_network_inspector\" --cmdLine=\\\"Init\\\" --cmdLine=\\\"{2} {3}\\\" --cmdLine=\\\"Fini\\\"\" {4}".format(network['topo'], x, test['motif'], y, config, p)

