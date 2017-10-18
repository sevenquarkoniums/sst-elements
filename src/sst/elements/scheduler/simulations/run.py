#!/usr/bin/env python
'''
Created by  : Yijia Zhang
Description : create workload and run a batch of sst jobs.

run by:
    ./run.py gen 1000
        :generate the random workloads.
    ./run.py empty
        :run single job on empty machine to get the baseline communication time.
    ./run.py run
        :run workload.

### TODO ###

### warning ###
Original ember output are modified for our task.
test with isolated=True before running new parameters.
opticalsPerRouter cannot be odd number for no reason.
allpingpong cannot work well for small mesIter.
adaptive iterations only work for alltoall 1000.
41 group experiments may fail due to memory 2G.

'''
import sys
#====================================
#----- queue variables -----#
qsub = True# whether qsub the program.
setQueue = False
if setQueue:
    queue = 'bme.q,icsg.q' #bme.q, ece.q, me.q is great.
useMoreMemory = False
if useMoreMemory:
    memory = 3

#----- debug variables -----#
runOnlyOne = True# submit only the first loop.
isolated = False# whether to use the isolated/ folder to generate output files.

#----- simulation parameters -----#
mode = sys.argv[1]# gen, empty, run.

nodeOneRouters = [4]
routersPerGroups = [8]
groupNums = [33]# use 3G for 65-group.
alphas = [4, 1, 0.25]# print as %.2f number.
utilizations = [90, 70] # machine utilization level.

mappers = ['topo'] # if want to change this, need to change the sst input file.
routings = ['adaptive_local']#['minimal', 'valiant', 'adaptive_local']
schedulers = ['easy']
applications = ['halo2d','fft','stencil','bcast','halo3d26','alltoall']# remove fft when use large messageSize.
messageSizes = [1000]#[10**x for x in range(1,6)]# not useful in fft. overwritten by workloads.
messageIters = [1]#[2**x for x in range(10)]# overwritten by workloads.
expIters = 10# iteration time of each experiment.

multipleRandomOrder = True# whether to have multiple cases of random allocation order through the expIters.

if mode == 'run':
    traceModes = ['corner']# corner, random, order.
    if 'random' in traceModes:
        multipleRandomOrder = False
    allocations = ['simple', 'random', 'dflyrdr', 'dflyrdg', 'dflyrrn', 'dflyrrr', 'dflyslurm', 'dflyhybrid']#,'dflyhybridbf','dflyhybridthres2','dflyhybridrn']
    hybridFolder = 'machine_4_8_33_2'# avoided by isolated.
    specificCornerCases = [69]#[1,2,3,18,6,22,26,27]
    modifyiters = []#[340,114,43,20,7,3]
    randomNum = 1000# only used for random workload.

elif mode == 'empty':
    traceModes = ['empty']
    allocations = ['simple', 'random', 'dflyrdr', 'dflyrdg', 'dflyrrn', 'dflyrrr', 'dflyslurm']
    emptySizes = [2,4,8,16,32,64,128]
    emptyFolder = 'empty_more'

elif mode == 'gen':
    multipleRandomOrder = False
    traceModes = ['random']
    randomNum = int(sys.argv[2])
    modifyiters = []

#====================================
#----- folder variables -----#
main_sim_path = "/mnt/nokrb/zhangyj/SST/scratch/src/sst-elements/src/sst/elements/scheduler/simulations"
env_script = "/mnt/nokrb/zhangyj/SST/exportSST.sh" # only modifys the environment variables.

useUnstrMotif = False# not recommended.
emberSimulation = True

import os, sys
import pandas as pd
from optparse import OptionParser
import os.path

def main():

    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option("-c",  action='store_true', dest="check", help="Check the experiment file names.")
    parser.add_option("-f",  action='store_true', dest="force", help="Force the experiment, will clobber old results.") # overide old results
    #parser.add_option("-e",  action='store', dest="exp_folder", help="Main experiment folder that holds all subfolders of the experiment.")
    (options, args) = parser.parse_args()

    if options.check:
        print("Action : Checking experiment file names")
    else:
        print("Action : Launching experiment")

    options.main_sim_path = main_sim_path
    options.env_script = env_script

    if isolated:
        print('Results will be in folder isolated/.')

    if mode == 'run':
        if isolated:
            options.exp_folder = 'isolated'
        else:
            options.exp_folder = hybridFolder
    elif mode == 'empty':
        options.exp_folder = emptyFolder

    simfileNames = []
    for gnidx, groupNum in enumerate(groupNums):
        routersPerGroup = routersPerGroups[gnidx]
        nodeOneRouter = nodeOneRouters[gnidx]

        nodeInGroup = routersPerGroup * nodeOneRouter
        # hosts_per_router, routers_per_group, intergroup_per_router, num_groups.
        options.dflyShape = '%d:%d:%d:%d' % (nodeOneRouter, routersPerGroup, 1, groupNum)# input into ember.
        opticalsPerRouter = int( (groupNum - 1) / routersPerGroup )
        # routersPerGroup, portsPerRouter, opticalsPerRouter, nodesPerRouter.
        dflyArgv = '%d,%d,%d,%d' % (routersPerGroup, nodeOneRouter + routersPerGroup - 1 + opticalsPerRouter, opticalsPerRouter, nodeOneRouter)# input into scheduler.

        for utilization in utilizations:
            nodesToAlloc = int(nodeInGroup * groupNum * utilization/100)
            for messageSize in messageSizes:
                for messageIter in messageIters:
                    for application in applications:
                        if application in ['alltoall','allpingpong','fft','bcast','halo3d26','halo2d']:
                            phasefileName = '%s_mesSize%d_mesIter%d.phase' % (application, messageSize, messageIter)
                            if not os.path.isfile('phase_files/%s' % phasefileName):
                                generatePhasefile(phasefileName, application, messageSize, messageIter)
                            if mode != 'empty':
                                # generate more phasefiles for the increased iterations of the smaller jobs.
                                for modifyiter in modifyiters:
                                    modifyname = '%s_mesSize%d_mesIter%d.phase' % (application, messageSize, modifyiter)
                                    generatePhasefile(modifyname, application, messageSize, modifyiter)
                        elif application == 'stencil':
                            phasefileName = '%s_mesIter%d.phase' % (application, messageIter)
                            if not os.path.isfile('phase_files/%s' % phasefileName):
                                generatePhasefile(phasefileName, 'halo3d', messageSize, messageIter)
                            if mode != 'empty':
                                for modifyiter in modifyiters:
                                    modifyname = '%s_mesSize%d_mesIter%d.phase' % (application, messageSize, modifyiter)
                                    generatePhasefile(modifyname, application, messageSize, modifyiter)
                        for traceMode in traceModes:
                            if traceMode == 'corner':
                                traceNumSet = specificCornerCases
                            elif traceMode == 'random':
                                traceNum = randomNum
                                traceNumSet = range(1, traceNum + 1)
                            elif traceMode == 'order':
                                traceNum = 50
                                traceNumSet = range(1, traceNum + 1)
                            elif traceMode == 'empty':
                                if isolated:
                                    traceNumSet = [8]
                                else:
                                    #traceNumSet = readTraceSet(groupNum, routersPerGroup, nodeOneRouter, messageSize, messageIter, application)
                                    traceNumSet = emptySizes

                            for traceNum in traceNumSet:
                                # trace numbers start from 1.
                                name1 = 'G%dR%dN%d_uti%d_%s_mesSize%d_mesIter%d_%s_%d' % (groupNum, routersPerGroup, nodeOneRouter, 
                                        utilization, application, messageSize, messageIter, traceMode, traceNum)
                                if not multipleRandomOrder:
                                    simfileName = name1 + '.sim'
                                    simfileNames.append(simfileName)
                                    if traceMode != 'random' and traceMode != 'order':
                                        generateSimfile(simfileName, nodesToAlloc, nodeOneRouter, routersPerGroup, groupNum, traceMode, traceNum, 
                                                graphName='empty', phaseName=phasefileName, runtime=1000)
                                    if mode == 'gen' and traceMode == 'random':
                                        generateSimfile(simfileName, nodesToAlloc, nodeOneRouter, routersPerGroup, groupNum, traceMode, traceNum, 
                                                graphName='empty', phaseName=phasefileName, runtime=1000)
                                        continue
                                    if mode == 'gen' and traceMode == 'order':
                                        orderedSimfile(simfileName, traceNum, phasefileName, runtime=1000)
                                        continue
                                    for allocator in allocations:
                                        for mapper in mappers:
                                            for scheduler in schedulers:
                                                name2 = '_%s_%s_%s' % (allocator, mapper, scheduler)
                                                options.sstInputName = name1 + name2 + '.py'
                                                generatePyfile(options.sstInputName, simfileName, application, mapper, dflyArgv, allocator)
                                                for rout in routings:
                                                    routName = 'adaptive' if rout == 'adaptive_local' else rout
                                                    for alpha in alphas:
                                                        for expIter in range(expIters):
                                                            name3 = '_%s_alpha%.2f_expIter%d' % (routName, alpha, expIter)
                                                            options.exp_name = name1 + name2 + name3
                                                            options.alpha = alpha
                                                            options.routing = rout
                                                            submit_job(options)
                                                            if runOnlyOne:
                                                                sys.exit(0)
                                elif multipleRandomOrder:# just move the for loop of expIter to the front and add expIter label to files.
                                    for expIter in range(expIters):
                                        simfileName = name1 + '_%d.sim' % expIter
                                        simfileNames.append(simfileName)
                                        generateSimfile(simfileName, application, nodesToAlloc, nodeOneRouter, routersPerGroup, groupNum, traceMode, traceNum, messageSize,
                                                graphName='empty', phaseName=phasefileName, runtime=1000)
                                        for allocator in allocations:
                                            for mapper in mappers:
                                                for scheduler in schedulers:
                                                    name2 = '_%s_%s_%s' % (allocator, mapper, scheduler)
                                                    options.sstInputName = name1 + name2 + '_%d.py' % expIter
                                                    generatePyfile(options.sstInputName, simfileName, application, mapper, dflyArgv, allocator)
                                                    for rout in routings:
                                                        routName = 'adaptive' if rout == 'adaptive_local' else rout
                                                        for alpha in alphas:
                                                            name3 = '_%s_alpha%.2f_expIter%d' % (routName, alpha, expIter)
                                                            options.exp_name = name1 + name2 + name3
                                                            options.alpha = alpha
                                                            options.routing = rout
                                                            submit_job(options)
                                                            if runOnlyOne:
                                                                sys.exit(0)


    if mode == 'gen':
        df = jobsizeDist(simfileNames)
        df.to_csv('jobsizeDist%d.csv' % randomNum, index=False)


#----- main end -----#
def jobsizeDist(simfileNames):
    sizeCount = {}
    for simfile in simfileNames:
        f = open('jobtrace_files/'+simfile, 'r')
        for line in f:
            linesplit = line.split()
            size = int(linesplit[1]) / 2
            if size not in sizeCount:
                sizeCount[size] = 1
            else:
                sizeCount[size] += 1

    df = pd.DataFrame(columns=['jobsize','count'])
    for jobsize in sizeCount:
        df.loc[len(df)] = [jobsize, sizeCount[jobsize]]
    print('jobsize distribution count finished.')
    return df

def readTraceSet(groupNum, routersPerGroup, nodeOneRouter, messageSize, messageIter, application):
    '''
    read all the encountered job size in the simulated hybrid workloads.
    Executing this funtion to get job size is not necessary.
    '''
    sizeFile = open('allsize_%s.txt' % application,'r')
    sizes = []
    for line in sizeFile:
        sizes.append( int(line) )
    return sizes

#def generateMyLoadfile(options, graphName, strategy, messageIter, messageSize):
#    '''
#    this function is obsolete now.
#    messageSize: only for alltoall motif.
#    '''
#    import random
#    # set the number of nodes needed by each job.
#    jobs = []
#    # the following is for sNum + lNum hybrid job.
#    for i in range(sNum):
#        jobs.append(int(nodeInGroup * sSize))
#    for i in range(lNum):
#        jobs.append(int(nodeInGroup * lSize))
#    
#    # stores the allocation method. 1st for job number. 2nd for node numbers of each job.
#    allocation = [[] for i in range(len(jobs))]
#    # 2-d list shows available nodes. 1st for group, 2st for node.
#    freeNode = [[] for i in range(groupNum)]
#    nodeNum = nodeInGroup * groupNum
#    for inode in range(nodeNum):
#        freeNode[int(inode/nodeInGroup)].append(inode)
#    
#    if strategy == 'simple':
#        currentGroup = 0
#        for ijob, job in enumerate(jobs):
#            while(job != 0):
#                if len(freeNode[currentGroup]) != 0:
#                    allocNode = freeNode[currentGroup][0]
#                    freeNode[currentGroup].remove(allocNode)
#                else:
#                    currentGroup += 1
#                    if currentGroup == groupNum:
#                        currentGroup = 0
#                    continue
#                allocation[ijob].append(allocNode)
#                job -= 1
#    elif strategy == 'simpleHeadEnd':# choose the head then the end when allocating in one group.
#        currentGroup = 0
#        eta = 0
#        for ijob, job in enumerate(jobs):
#            while(job != 0):
#                if len(freeNode[currentGroup]) != 0:
#                    allocNode = freeNode[currentGroup][eta]
#                    freeNode[currentGroup].remove(allocNode)
#                    if eta == 0:
#                        eta = -1
#                    elif eta == -1:
#                        eta = 0
#                else:
#                    currentGroup += 1
#                    if currentGroup == groupNum:
#                        currentGroup = 0
#                    continue
#                allocation[ijob].append(allocNode)
#                job -= 1
#    elif strategy == 'simpleRandom':# random choose a node when allocating in one group.
#        currentGroup = 0
#        for ijob, job in enumerate(jobs):
#            while(job != 0):
#                if len(freeNode[currentGroup]) != 0:
#                    allocNode = random.choice(freeNode[currentGroup])
#                    freeNode[currentGroup].remove(allocNode)
#                else:
#                    currentGroup += 1
#                    if currentGroup == groupNum:
#                        currentGroup = 0
#                    continue
#                allocation[ijob].append(allocNode)
#                job -= 1
#    elif strategy == 'spreadLimited':# only works for a single job. spread but limited in the condensed groups.
#        currentGroup = 0
#        for ijob, job in enumerate(jobs):
#            while(job != 0):
#                if len(freeNode[currentGroup]) != 0:
#                    allocNode = freeNode[currentGroup][0]
#                    #allocNode = random.choice(freeNode[currentGroup])# randomness in selection.
#                    freeNode[currentGroup].remove(allocNode)
#                else:
#                    currentGroup += 1
#                    if currentGroup == groupNum:
#                        currentGroup = 0
#                    continue
#                allocation[ijob].append(allocNode)
#                currentGroup += 1# change group when successfully allocate a job.
#                if currentGroup == sSize:
#                    currentGroup = 0
#                job -= 1
#    elif strategy == 'localSpread':# select one node and jump to next router in the same group.
#        currentGroup = 0
#        currentNode = 0
#        for ijob, job in enumerate(jobs):
#            while(job != 0):
#                if len(freeNode[currentGroup]) != 0:
#                    allocNode = freeNode[currentGroup][currentNode]
#                    freeNode[currentGroup].remove(allocNode)
#                    currentNode += 1
#                    if currentNode >= freeNode[currentGroup]:
#                        currentNode = 0
#                else:
#                    currentGroup += 1
#                    if currentGroup == groupNum:
#                        currentGroup = 0
#                    continue
#                allocation[ijob].append(allocNode)
#                job -= 1
#    elif strategy == 'spread':
#        currentGroup = 0
#        for ijob, job in enumerate(jobs):
#            while(job != 0):
#                if len(freeNode[currentGroup]) != 0:
#                    allocNode = freeNode[currentGroup][0]# add randomness in this line.
#                    freeNode[currentGroup].remove(allocNode)
#                else:
#                    currentGroup += 1
#                    if currentGroup == groupNum:
#                        currentGroup = 0
#                    continue
#                allocation[ijob].append(allocNode)
#                currentGroup += 1# change group when successfully allocate a job.
#                if currentGroup == groupNum:
#                    currentGroup = 0
#                job -= 1
#    elif strategy == 'nodeSpread':# allocate all 2 nodes in a router then change to next group.
#        currentGroup = 0
#        for ijob, job in enumerate(jobs):
#            while(job != 0):
#                if len(freeNode[currentGroup]) != 0:
#                    allocNode = freeNode[currentGroup][0]# add randomness in this line.
#                    freeNode[currentGroup].remove(allocNode)
#                else:
#                    currentGroup += 1
#                    if currentGroup == groupNum:
#                        currentGroup = 0
#                    continue
#                allocation[ijob].append(allocNode)
#                if allocNode % 2 == 1:
#                    currentGroup += 1# change group when an odd number node is allocated.
#                if currentGroup == groupNum:
#                    currentGroup = 0
#                job -= 1
#    elif strategy == 'spreadRandom':
#        currentGroup = 0
#        for ijob, job in enumerate(jobs):
#            while(job != 0):
#                if len(freeNode[currentGroup]) != 0:
#                    allocNode = random.choice(freeNode[currentGroup])
#                    freeNode[currentGroup].remove(allocNode)
#                else:
#                    currentGroup += 1
#                    if currentGroup == groupNum:
#                        currentGroup = 0
#                    continue
#                allocation[ijob].append(allocNode)
#                currentGroup += 1# change group when successfully allocate a job.
#                if currentGroup == groupNum:
#                    currentGroup = 0
#                job -= 1
#    elif strategy == 'hybrid':
#        # add the grouped ones first serially. mark the nodes as allocated.
#        for ialloc in range(sNum):
#            allocation[ialloc] = list(range(int(nodeInGroup * sSize * ialloc), int(nodeInGroup * sSize * (ialloc+1))))
#            # this works only if no small job occupys part of a group.
#            freeNode[int(ialloc * sSize)] = []
#
#        currentGroup = 0
#        for ijob, job in enumerate(jobs):
#            # jump the allocated jobs.
#            if ijob < sNum:
#                continue
#
#            while(job != 0):
#                if len(freeNode[currentGroup]) != 0:
#                    allocNode = freeNode[currentGroup][0]# add randomness in this line.
#                    freeNode[currentGroup].remove(allocNode)
#                else:
#                    currentGroup += 1
#                    if currentGroup == groupNum:
#                        currentGroup = 0
#                    continue
#                allocation[ijob].append(allocNode)
#                currentGroup += 1# change group when successfully allocate a job.
#                if currentGroup == groupNum:
#                    currentGroup = 0
#                job -= 1
#    
#    elif strategy == 'hybridRandom':
#        # add the grouped ones first serially. mark the nodes as allocated.
#        for ialloc in range(sNum):
#            allocation[ialloc] = list(range(int(nodeInGroup * sSize * ialloc), int(nodeInGroup * sSize * (ialloc+1))))
#            # this works only if no small job occupys part of a group.
#            freeNode[int(ialloc * sSize)] = []
#
#        currentGroup = 0
#        for ijob, job in enumerate(jobs):
#            # jump the allocated jobs.
#            if ijob < sNum:
#                continue
#
#            while(job != 0):
#                if len(freeNode[currentGroup]) != 0:
#                    allocNode = random.choice(freeNode[currentGroup])
#                    freeNode[currentGroup].remove(allocNode)
#                else:
#                    currentGroup += 1
#                    if currentGroup == groupNum:
#                        currentGroup = 0
#                    continue
#                allocation[ijob].append(allocNode)
#                currentGroup += 1# change group when successfully allocate a job.
#                if currentGroup == groupNum:
#                    currentGroup = 0
#                job -= 1
#    elif strategy == 'random':
#        freeGroup = [x for x in range(groupNum)]
#        for ijob, job in enumerate(jobs):
#            while(job != 0):
#                currentGroup = random.choice(freeGroup)
#                if len(freeNode[currentGroup]) != 0:
#                    allocNode = random.choice(freeNode[currentGroup])
#                    freeNode[currentGroup].remove(allocNode)
#                else:
#                    freeGroup.remove(currentGroup)
#                    continue
#                allocation[ijob].append(allocNode)
#                job -= 1
#
#    if shuffle:
#        for job in allocation:
#            random.shuffle(job)
#
#    # parameters for this part are in ember.cc.
#    fo = open(options.outdir + '/myloadfile','w')
#    for ijob, jobAlloc in enumerate(allocation):
#        fo.write('[JOB_ID] %d\n' % ijob)
#        fo.write('\n')
#        fo.write('[NID_LIST] ')
#        fo.write(','.join(str(x) for x in jobAlloc))
#        fo.write('\n')
#        fo.write('[MOTIF] Init\n')
#        if options.application == 'mesh':
#            fo.write('[MOTIF] Halo3D iterations=%d doreduce=0 pex=4 pey=4 pez=4\n' % messageIter)# number should change.
#        elif options.application == 'alltoall':
#            if ijob < sNum:# for small job.
#                if useUnstrMotif == True:
#                    fo.write('[MOTIF] Unstructured iterations=%d\tgraphfile=graph_files/%s\n' % (messageIter, graphName[0]) )
#                else:
#                    fo.write('[MOTIF] Alltoall iterations=%d\tbytes=%d\n' % (messageIter, messageSize) )
#            else:# for large jobs.
#                if useUnstrMotif == True:
#                    fo.write('[MOTIF] Unstructured iterations=%d\tgraphfile=graph_files/%s\n' % (messageIter, graphName[1]) )
#                else:
#                    fo.write('[MOTIF] Alltoall iterations=%d\tbytes=%d\n' % (messageIter, messageSize) )
#        fo.write('[MOTIF] Fini\n')
#        fo.write('\n')
#    fo.close()


def generatePyfile(sstInputName, simfileName, application, mapper, dflyArgv, allocator):
    '''
    use makeInput.py to generate the python input file for SST-scheduler module.
    '''
    pyName = 'sstInput/%s' % sstInputName
    detailedEmber = 'ON' if emberSimulation else 'OFF'
    simfileAddr = 'jobtrace_files/%s' % simfileName
    os.system('./makeInput.py %s %s %s %s %s' % (simfileAddr, pyName, dflyArgv, allocator, detailedEmber) )
    print('sstInput %s generated.' % pyName)
    # the following is the obsolete generating method.
    #lines = open('pyfileTemplateR%dG%d.py' % (routersPerGroup, groupNum) ).read().splitlines()# template.
    #wlines = []# making a copy and make change on that copy.
    #for row in lines:
    #    if 'traceName' in row:# "traceName" : "jobtrace_files/alltoall_N8.sim",
    #        sim = row.split('\"')[3]
    #        sim = sim.split('/')[1]
    #        row = row.replace(sim, simfileName)
    #    elif 'taskMapper' in row:# "taskMapper" : "topo",
    #        currentMapper = row.split('\"')[3]
    #        if mapper == 'simple':
    #            row = row.replace(currentMapper, mapper)
    #        elif mapper == 'libtopomap':
    #            row = row.replace(currentMapper, 'topo')
    #        elif mapper == 'random':
    #            row = row.replace(currentMapper, 'random')
    #    wlines.append(row)
    #pyName = '%s.py' % (pyName)
    #pyo = open(pyName,'w')
    #pyo.write('\n'.join(wlines))
    #pyo.close()


#def changeSnapSched(expectR, expectShape, expectMyload):
#    '''
#    change the parameters in snapshotParser_sched.py.
#    '''
#    snapold = open('snapshotParser_sched.py')
#    lines = snapold.read().splitlines()
#    wlines = []
#    for row in lines:
#        if 'routing =' in row:# routing = 'valiant'.
#            currentR = row.split('\'')[1]
#            row = row.replace(currentR, expectR)
#        elif 'useMyLoadfile = ' in row:# useMyLoadfile = False# name: myloadfile.
#            currentMyload = row.split('=')[1]
#            currentMyload = currentMyload.split('#')[0]
#            currentMyload = currentMyload[1:]
#            row = row.replace(currentMyload, expectMyload)
#        elif row.startswith('dragonPara'):# dragonPara = '2:4:1:17' # hosts_per_router, routers_per_group, intergroup_per_router, num_groups.
#            currentShape = row.split('\'')[1]
#            row = row.replace(currentShape, expectShape)
#        
#        wlines.append(row)
#    snapold.close()
#    snap = open('snapshotParser_sched.py','w')
#    snap.write('\n'.join(wlines))
#    snap.close()
#    print('snapshotParser_sched.py modified.')

def generateSimfile(simName, application, nodesToAlloc, nodeOneRouter, routersPerGroup, groupNum, traceMode, traceNum, messageSize, graphName, phaseName, runtime):
    '''
    generate the .sim files in the jobtrace_file folder.
    Workloads are generated in this function.

    traceMode = 'corner' generate corner cases.
                'empty' generate empty machine traces.
                'random' generate random cases.

    runtime is an int in microseconds setting the assumed running time of a job. Not useful.
    '''
    import random
    from random import shuffle
    import math
    tempname = 'jobtrace_files/' + simName
    simfile = open(tempname, 'w')
    if traceMode == 'empty':
        node = traceNum
        core = node * 2
        simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
        simfile.write(simLine)

    elif traceMode == 'corner':
        # some corner cases.
        #if traceNum == 1:
        #    node = 2
        #    core = node * 2
        #    jobNum = int(nodesToAlloc / node)
        #    for ijob in range(jobNum):
        #        simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
        #        simfile.write(simLine)
        if traceNum == 1:
            node = nodeOneRouter
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 2:
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 3:
            node = 2 * nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 4:# replaced by 18.
            node = int(nodeOneRouter * routersPerGroup * groupNum / 2) # the case that all jobs are large.
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        #elif traceNum == 5:
        #    node = nodeOneRouter
        #    core = node * 2
        #    jobNum = int( ( nodesToAlloc - int(nodesToAlloc / 4) ) / 2 )
        #    for ijob in range(jobNum):
        #        simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
        #        simfile.write(simLine)
        #    node = int(nodesToAlloc / 4)
        #    core = node * 2
        #    simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
        #    simfile.write(simLine)
        elif traceNum == 5:
            node = nodeOneRouter + 1
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 6:
            node = nodeOneRouter * routersPerGroup + 1
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 7:
            # large ones.
            node = 2 * nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(2):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # small ones.
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - 4 * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 8:
            # small ones.
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - 4 * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # large ones.
            node = 2 * nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(2):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 9:
            # large ones.
            node = 2 * nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(2):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # small ones.
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = int( ( nodesToAlloc - 4 * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 10:
            # small ones.
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = int( ( nodesToAlloc - 4 * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # large ones.
            node = 2 * nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(2):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 11:
            # large ones.
            node = 5 * nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = 2
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # medium ones.
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = 3
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # small ones.
            node = nodeOneRouter
            core = node * 2
            jobNum = 16
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 12:
            # small ones.
            node = nodeOneRouter
            core = node * 2
            jobNum = 16
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # medium ones.
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = 3
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # large ones.
            node = 5 * nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = 2
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 13:
            # medium ones.
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = 3
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # large ones.
            node = 5 * nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = 2
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # small ones.
            node = nodeOneRouter
            core = node * 2
            jobNum = 16
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 14:
            node = 3 * nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 15:
            node = 4 * nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 16:# No.7 with mixed iterations.
            # large ones.
            node = 2 * nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(2):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # small ones amplified.
            phaseName = 'alltoall_mesSize1000_mesIter100.phase'
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - 4 * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 17:# No.7 with median instead of large.
            # median ones.
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(2):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # small ones. 
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - 2 * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 18:# replacing case 4, here each job is quarter-size.
            node = int(nodeOneRouter * routersPerGroup * groupNum / 4)
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        #elif traceNum == 9:
        #    # large ones.
        #    node = int(nodeOneRouter * routersPerGroup * groupNum / 2)
        #    core = node * 2
        #    phaseName = 'alltoall_mesSize1000_mesIter1.phase'
        #    simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
        #    simfile.write(simLine)
        #    # small ones.
        #    node = nodeOneRouter
        #    core = node * 2
        #    jobNum = int( ( nodesToAlloc - int(nodeOneRouter * routersPerGroup * groupNum / 2) ) / node )
        #    for ijob in range(jobNum):
        #        phaseName = 'alltoall_mesSize1000_mesIter100.phase'
        #        simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
        #        simfile.write(simLine)
        elif traceNum == 19:# No.7 with mixed message size.
            # large ones.
            node = 2 * nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(2):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # small ones amplified.
            phaseName = 'alltoall_mesSize10000000_mesIter1.phase'
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - 4 * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 20:
            # median ones.
            node = 8
            core = node * 2
            for ijob in range(1):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # large ones. 
            node = 32
            core = node * 2
            jobNum = 2
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 21:# 5 jobs for the G9R4N2 machine.
            for ijob in range(1, 5+1):
                node = 2**ijob
                core = node * 2
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 22:# R-level and G-level jobs.
            # median ones.
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(int(groupNum/2)):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # small ones. 
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - int(groupNum/2) * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 23:# no.22 with small ones amplified.
            # median ones.
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(9):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # small ones. 
            phaseName = 'alltoall_mesSize1000_mesIter100.phase'
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - 9 * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 24:# G-level and 4 M-level jobs.
            # big ones.
            node = 2 * nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(4):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # median ones. 
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = int( ( nodesToAlloc - 8 * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 25:# G-level and M-level jobs.
            # big ones.
            node = 2 * nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(4):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # median ones. 
            phaseName = 'alltoall_mesSize1000_mesIter100.phase'
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = int( ( nodesToAlloc - 8 * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 26:# many G-level jobs and 2 quarter-size jobs.
            # median ones. 
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = int( ( nodesToAlloc - int(nodeOneRouter * routersPerGroup * groupNum / 2) ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # big ones.
            node = int(nodeOneRouter * routersPerGroup * groupNum / 4)
            core = node * 2
            for ijob in range(2):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 27:# R-level and M-level jobs.
            # large ones.
            node = int(nodeOneRouter * routersPerGroup * groupNum / 4)
            core = node * 2
            for ijob in range(2):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
            # small ones. 
            phaseName = 'alltoall_mesSize1000_mesIter42.phase'
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - int(nodeOneRouter * routersPerGroup * groupNum / 2) ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 28:# order-randomized R-level and M-level jobs.
            strings = []
            # large ones.
            node = int(nodeOneRouter * routersPerGroup * groupNum / 4)
            core = node * 2
            for ijob in range(2):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                strings.append(simLine)
            # small ones. 
            phaseName = 'alltoall_mesSize1000_mesIter42.phase'
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - int(nodeOneRouter * routersPerGroup * groupNum / 2) ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 29:# randomized many G-level jobs and 2 quarter-size jobs.
            strings = []
            # big ones.
            node = int(nodeOneRouter * routersPerGroup * groupNum / 4)
            core = node * 2
            for ijob in range(2):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                strings.append(simLine)
            # median ones. 
            phaseName = 'alltoall_mesSize1000_mesIter7.phase'
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = int( ( nodesToAlloc - int(nodeOneRouter * routersPerGroup * groupNum / 2) ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 30:# randomized R-level and G-level jobs.
            strings = []
            # median ones.
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            for ijob in range(int(groupNum/2)):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                strings.append(simLine)
            # small ones. 
            phaseName = 'alltoall_mesSize1000_mesIter6.phase'
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - int(groupNum/2) * nodeOneRouter * routersPerGroup ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 31:# 1 small and 4 large.
            strings = []
            # small ones.
            phaseName2 = 'alltoall_mesSize1000_mesIter40.phase'
            node = nodeOneRouter
            core = node * 2
            for ijob in range(1):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
                strings.append(simLine)
            # large ones. 
            node = int( ( nodesToAlloc - nodeOneRouter ) / 4 )
            core = node * 2
            jobNum = 4
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 32:# 1 large and many small.
            strings = []
            # small ones.
            phaseName2 = 'alltoall_mesSize1000_mesIter42.phase'
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - int(groupNum * nodeOneRouter * routersPerGroup / 4) ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
                strings.append(simLine)
            # large ones.
            node = int(nodeOneRouter * routersPerGroup * groupNum / 4)
            core = node * 2
            jobNum = 1
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 33:# 2 & 4. 1 small and many large.
            strings = []
            # small ones.
            phaseName2 = 'alltoall_mesSize1000_mesIter340.phase'
            node = 2
            core = node * 2
            jobNum = 1
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
                strings.append(simLine)
            # large ones.
            phaseName3 = 'alltoall_mesSize1000_mesIter114.phase'
            node = 4
            core = node * 2
            jobNum = int( (nodesToAlloc - 2) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName3)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 34:# 2 & 8. 1 small and many large.
            strings = []
            # small ones.
            phaseName2 = 'alltoall_mesSize1000_mesIter340.phase'
            node = 2
            core = node * 2
            jobNum = 1
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
                strings.append(simLine)
            # large ones.
            phaseName3 = 'alltoall_mesSize1000_mesIter43.phase'
            node = 8
            core = node * 2
            jobNum = int( (nodesToAlloc - 2) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName3)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 35:# 2 & 16. 1 small and many large.
            strings = []
            # small ones.
            phaseName2 = 'alltoall_mesSize1000_mesIter340.phase'
            node = 2
            core = node * 2
            jobNum = 1
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
                strings.append(simLine)
            # large ones.
            phaseName3 = 'alltoall_mesSize1000_mesIter20.phase'
            node = 16
            core = node * 2
            jobNum = int( (nodesToAlloc - 2) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName3)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 36:# 4 & 8. 1 small and many large.
            strings = []
            # small ones.
            phaseName2 = 'alltoall_mesSize1000_mesIter114.phase'
            node = 4
            core = node * 2
            jobNum = 1
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
                strings.append(simLine)
            # large ones.
            phaseName3 = 'alltoall_mesSize1000_mesIter43.phase'
            node = 8
            core = node * 2
            jobNum = int( (nodesToAlloc - 4) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName3)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 37:# 4 & 16. 1 small and many large.
            strings = []
            # small ones.
            phaseName2 = 'alltoall_mesSize1000_mesIter114.phase'
            node = 4
            core = node * 2
            jobNum = 1
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
                strings.append(simLine)
            # large ones.
            phaseName3 = 'alltoall_mesSize1000_mesIter20.phase'
            node = 16
            core = node * 2
            jobNum = int( (nodesToAlloc - 4) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName3)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 38:# 8 & 16. 1 small and many large.
            strings = []
            # small ones.
            phaseName2 = 'alltoall_mesSize1000_mesIter43.phase'
            node = 8
            core = node * 2
            jobNum = 1
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
                strings.append(simLine)
            # large ones.
            phaseName3 = 'alltoall_mesSize1000_mesIter20.phase'
            node = 16
            core = node * 2
            jobNum = int( (nodesToAlloc - 8) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName3)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 39:# 8 & 16. 2 small and many large.
            strings = []
            # small ones.
            phaseName2 = 'alltoall_mesSize1000_mesIter43.phase'
            node = 8
            core = node * 2
            jobNum = 2
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
                strings.append(simLine)
            # large ones.
            phaseName3 = 'alltoall_mesSize1000_mesIter20.phase'
            node = 16
            core = node * 2
            jobNum = int( (nodesToAlloc - 16) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName3)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 40:# 8 & 16. 3 small and many large.
            strings = []
            # small ones.
            phaseName2 = 'alltoall_mesSize1000_mesIter43.phase'
            node = 8
            core = node * 2
            jobNum = 3
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
                strings.append(simLine)
            # large ones.
            phaseName3 = 'alltoall_mesSize1000_mesIter20.phase'
            node = 16
            core = node * 2
            jobNum = int( (nodesToAlloc - 24) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName3)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 41:# 8 & 16. 4 small and many large.
            strings = []
            # small ones.
            phaseName2 = 'alltoall_mesSize1000_mesIter43.phase'
            node = 8
            core = node * 2
            jobNum = 4
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
                strings.append(simLine)
            # large ones.
            phaseName3 = 'alltoall_mesSize1000_mesIter20.phase'
            node = 16
            core = node * 2
            jobNum = int( (nodesToAlloc - 32) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName3)
                strings.append(simLine)
            shuffle(strings)# randomized the allocation order.
            for string in strings:
                simfile.write(string)
        elif traceNum == 42:
            writeTrace('fixed', nodesToAlloc, simfile, runtime, 32, 8, 1, 16)
        elif traceNum == 43:
            writeTrace('fixed', nodesToAlloc, simfile, runtime, 1, 8, 16, 16)
        elif traceNum == 44:
            writeTrace('fixed', nodesToAlloc, simfile, runtime, 12, 8, 11, 16)
        elif traceNum == 45:
            writeTrace('fixed', nodesToAlloc, simfile, runtime, 6, 32, 1, 64)
        elif traceNum == 46:
            writeTrace('fixed', nodesToAlloc, simfile, runtime, 1, 32, 3, 64)
        elif traceNum == 47:
            writeTrace('fixed', nodesToAlloc, simfile, runtime, 4, 32, 2, 64)
        elif traceNum == 48:
            writeTrace('fixed', nodesToAlloc, simfile, runtime, 13, 16, 1, 64)
        elif traceNum == 49:
            writeTrace('fixed', nodesToAlloc, simfile, runtime, 1, 16, 4, 64)
        elif traceNum == 50:
            writeTrace('fixed', nodesToAlloc, simfile, runtime, 5, 16, 3, 64)
        elif traceNum == 51:
            writeTrace('equalNum', nodesToAlloc, simfile, runtime, -1, 2, -1, 4)
        elif traceNum == 52:
            node = 2 * nodeOneRouter
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 53:
            # small ones.
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = 5
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/alltoall_mesSize1000_mesIter20.phase\n' % (core, runtime)
                simfile.write(simLine)
            # large ones.
            node = 4 * nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = 3
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/alltoall_mesSize1000_mesIter3.phase\n' % (core, runtime)
                simfile.write(simLine)
        elif traceNum == 54:
            writeTrace('fixed', False, nodesToAlloc, simfile, runtime, 1, 16, 1000, 1, 4, 64, 1000, 20)
        elif traceNum == 55:
            writeTrace('fixed', False, nodesToAlloc, simfile, runtime, 1, 16, 10000, 1, 4, 64, 1000, 20)
        elif traceNum == 56:
            writeTrace('fixed', False, nodesToAlloc, simfile, runtime, 1, 16, 100000, 1, 4, 64, 1000, 20)
        elif traceNum == 57:
            writeTrace('fixed', False, nodesToAlloc, simfile, runtime, 1, 16, 1000, 10, 4, 64, 1000, 20)
        elif traceNum == 58:
            writeTrace('fixed', False, application, nodesToAlloc, simfile, runtime, 1, 16, 1000, 100, 4, 64, 10000, 1)
        elif traceNum == 59:
            writeTrace('fixed', False, application, nodesToAlloc, simfile, runtime, 1, 16, 1000, 100, 4, 64, 1000, 10)
        elif traceNum == 60:
            writeTrace('fixed', False, application, nodesToAlloc, simfile, runtime, 1, 16, 10000, 10, 4, 64, 1000, 10)
        elif traceNum == 61:
            writeTrace('fixed', False, application, nodesToAlloc, simfile, runtime, 1, 16, 100000, 1, 4, 64, 1000, 10)
        elif traceNum == 62:
            writeTrace('homo', False, application, nodesToAlloc, simfile, runtime, 0, 4, messageSize, 1)
        elif traceNum == 63:
            writeTrace('homo', False, application, nodesToAlloc, simfile, runtime, 0, 8, 1000, 1)
        elif traceNum == 64:
            writeTrace('homo', False, application, nodesToAlloc, simfile, runtime, 0, 16, messageSize, 1)
        elif traceNum == 65:
            writeTrace('homo', False, application, nodesToAlloc, simfile, runtime, 0, 32, 1000, 1)
        elif traceNum == 66:
            writeTrace('homo', False, application, nodesToAlloc, simfile, runtime, 0, 64, messageSize, 1)
        elif traceNum == 67:
            writeTrace('homo', False, application, nodesToAlloc, simfile, runtime, 0, 128, 1000, 1)
        elif traceNum == 68:
            writeTrace('homo', False, application, nodesToAlloc, simfile, runtime, 0, int(nodesToAlloc/4), messageSize, 1)# should use uti 100%.
        elif traceNum == 69:
            writeTrace('equalNum', False, application, nodesToAlloc, simfile, runtime, 0, 16, 1000, 2, 0, 64, 1000, 2)# the default messageSize are overwritten.
        elif traceNum == 70:
            writeTrace('equalNum', False, application, nodesToAlloc, simfile, runtime, 0, 16, 100000, 2, 0, 64, 100000, 2)
        elif traceNum == 71:
            writeTrace('equalNum', False, application, nodesToAlloc, simfile, runtime, 0, 16, 100000, 2, 0, 64, 1000, 2)
        elif traceNum == 72:
            writeTrace('equalNum', False, application, nodesToAlloc, simfile, runtime, 0, 16, 1000, 2, 0, 64, 100000, 2)

        elif (traceNum // 100)==1:# 1ij.
            i = traceNum // 10 - 10
            j = traceNum % 10
            writeTrace('equalNum', nodesToAlloc, simfile, runtime, -1, 2**i, -1, 2**j)
        elif traceNum >= 1000:# generate random number of two sizes of jobs, should meet the machine utilization level. allocate small jobs first.
            writeTrace('randomTwoSize', False, application, nodesToAlloc, simfile, runtime)

    elif traceMode == 'random':
        freeNode = nodesToAlloc
        totalNode = nodeOneRouter * routersPerGroup * groupNum
        jobID = 1
        while freeNode > 1:
            # make a new job.
            index = int(math.log(min([totalNode/2, freeNode]), 2))
            node = 2 ** random.randint(1, index)
            core = node * 2
            print('Job %d size: %d nodes' % (jobID, node) )
            arriveTime = 0

            #simLine = '%d %d %d -1 phase phase_files/%s\n' % (arriveTime, core, runtime, phaseName)
            if node == 2:
                phaseName2 = 'alltoall_mesSize1000_mesIter340.phase'
            elif node == 4:
                phaseName2 = 'alltoall_mesSize1000_mesIter114.phase'
            elif node == 8:
                phaseName2 = 'alltoall_mesSize1000_mesIter43.phase'
            elif node == 16:
                phaseName2 = 'alltoall_mesSize1000_mesIter20.phase'
            elif node == 32:
                phaseName2 = 'alltoall_mesSize1000_mesIter7.phase'
            elif node == 64:
                phaseName2 = 'alltoall_mesSize1000_mesIter3.phase'
            elif node == 128:
                phaseName2 = 'alltoall_mesSize1000_mesIter1.phase'
            simLine = '%d %d %d -1 phase phase_files/%s\n' % (arriveTime, core, runtime, phaseName2)

            simfile.write(simLine)
            freeNode = freeNode - node
            jobID = jobID + 1

    simfile.close()
    print('tracefile %s generated.' % simName)

def writeTrace(writemode, randomOrder, application, nodesToAlloc, simfile, runtime, num1=0, size1=0, mesSize1=0, mesIter1=0, num2=0, size2=0, mesSize2=0, mesIter2=0):
    from random import shuffle
    from random import randint
    strings = []
    if application == 'stencil':
        application = 'halo3d'

    # first size.
    node = size1
    core = node * 2
    if writemode == 'fixed':
        jobNum = num1
    elif writemode == 'equalNum':# assume size1 <= size2.
        jobNum = int(nodesToAlloc/(size1+size2))
    elif writemode == 'homo':# only one type of jobs.
        jobNum = int(nodesToAlloc/size1)
    elif writemode == 'randomTwoSize':
        size2 = randint(17, 270)
        jobNum2limit = int(nodesToAlloc/size2)
        jobNum2 = randint(1, jobNum2limit)
        size1 = randint(2, 16)

    if mesIter1 == 'auto':# if want to automatically change the iteration of messages to match the running of both small & large jobs.
        if node == 2:
            phaseName2 = 'alltoall_mesSize%d_mesIter340.phase' % mesSize1
        elif node == 4:
            phaseName2 = 'alltoall_mesSize%d_mesIter114.phase' % mesSize1
        elif node == 8:
            phaseName2 = 'alltoall_mesSize%d_mesIter43.phase' % mesSize1
        elif node == 16:
            phaseName2 = 'alltoall_mesSize%d_mesIter20.phase' % mesSize1
        elif node == 32:
            phaseName2 = 'alltoall_mesSize%d_mesIter7.phase' % mesSize1
        elif node == 64:
            phaseName2 = 'alltoall_mesSize%d_mesIter3.phase' % mesSize1
        elif node == 128:
            phaseName2 = 'alltoall_mesSize%d_mesIter1.phase' % mesSize1
    else:
        phaseName2 = '%s_mesSize%d_mesIter%d.phase' % (application, mesSize1, mesIter1)
        if not os.path.isfile('phase_files/%s' % phaseName2):
            generatePhasefile(phaseName2, application, mesSize1, mesIter1)
    for ijob in range(jobNum):
        simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
        strings.append(simLine)

    # second size.
    if writemode != 'homo':
        node = size2
        core = node * 2
        if writemode == 'fixed':
            jobNum = num2
        elif writemode == 'equalNum':# assume size1 <= size2.
            jobNum = int(nodesToAlloc/(size1+size2))
            #jobNum = int(nodesToAlloc/(size1+size2)) + int((nodesToAlloc-(size1+size2)*int(nodesToAlloc/(size1+size2)))/size2)

        if mesIter2 == 'auto':
            if node == 2:
                phaseName2 = 'alltoall_mesSize%d_mesIter340.phase' % mesSize2
            elif node == 4:
                phaseName2 = 'alltoall_mesSize%d_mesIter114.phase' % mesSize2
            elif node == 8:
                phaseName2 = 'alltoall_mesSize%d_mesIter43.phase' % mesSize2
            elif node == 16:
                phaseName2 = 'alltoall_mesSize%d_mesIter20.phase' % mesSize2
            elif node == 32:
                phaseName2 = 'alltoall_mesSize%d_mesIter7.phase' % mesSize2
            elif node == 64:
                phaseName2 = 'alltoall_mesSize%d_mesIter3.phase' % mesSize2
            elif node == 128:
                phaseName2 = 'alltoall_mesSize%d_mesIter1.phase' % mesSize2
        else:
            phaseName2 = '%s_mesSize%d_mesIter%d.phase' % (application, mesSize2, mesIter2)
            if not os.path.isfile('phase_files/%s' % phaseName2):
                generatePhasefile(phaseName2, application, mesSize2, mesIter2)
        for ijob in range(jobNum):
            simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName2)
            strings.append(simLine)

    if randomOrder == True:
        shuffle(strings)# randomized the allocation order.
    for string in strings:
        simfile.write(string)

def orderedSimfile(simName, traceNum, phaseName, runtime):
    '''
    To compare different allocation order of the seven jobs in size: 2 4 8 16 32 64 128.
    traceNum=1 is the small-first order.
    traceNum=2 is the large-first order.
    others are randomly generated order for allocation.
    '''
    from random import shuffle
    import math
    tempname = 'jobtrace_files/' + simName
    simfile = open(tempname, 'w')
    jobsizes = [2**x for x in range(1, 7+1)]
    rever = list(reversed(jobsizes))
    shuff = jobsizes
    if traceNum == 1:
        for ijob in range(len(jobsizes)):
            core = jobsizes[ijob] * 2
            simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
            simfile.write(simLine)
    elif traceNum == 2:
        for ijob in range(len(rever)):
            core = rever[ijob] * 2
            simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
            simfile.write(simLine)
    elif traceNum > 2:
        shuffle(shuff)
        for ijob in range(len(shuff)):
            core = shuff[ijob] * 2
            simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
            simfile.write(simLine)
    simfile.close()
    print('tracefile %s generated.' % simName)

def generatePhasefile(phaseName, pattern, messageSize=1000, messageIter=1, graphName='empty'):
    '''
    Motifs are defined in ember/mpi/motifs/.
    Motif parameters can be found in ember.cc
    Motif label name are in .cc files of ember/mpi/motifs/.
    '''
    tempname = 'phase_files/' + phaseName
    phasefile = open(tempname, 'w')
    phasefile.write('Init\n')
    if useUnstrMotif == True:
        phasefile.write('Unstructured\tgraphfile=graph_files/%s\n' % graphName)
    else:
        if pattern == 'alltoall':
            phasefile.write('Alltoall    iterations=%d    bytes=%d\n' % (messageIter, messageSize) )
        elif pattern == 'halo2d':
            phasefile.write('Halo2D    iterations=%d    messagesizex=%d    messagesizey=%d    computenano=1\n' % (messageIter, messageSize, messageSize))
        elif pattern == 'halo3d':
            phasefile.write('Halo3D    doreduce=1    iterations=%d    fields_per_cell=%d    computetime=1    nx=16    ny=16    nz=16\n' % (messageIter, messageSize/1000))
        elif pattern == 'halo3d26':
            phasefile.write('Halo3D26    doreduce=1    iterations=%d    fields_per_cell=%d    computetime=1    nx=16    ny=16    nz=16\n' % (messageIter, messageSize/1000))
        elif pattern == 'allpingpong':# weird results, too small.
            phasefile.write('AllPingPong    iterations=%d    messageSize=%d    computetime=1\n' % (messageIter, messageSize) )
        elif pattern == 'fft':
            phasefile.write('FFT3D    iterations=%d    npRow=4\n' % (messageIter) )
        elif pattern == 'bcast':
            phasefile.write('Bcast    iterations=%d    count=%d\n' % (messageIter, messageSize) )# the count isn't messageSize.
    phasefile.write('Fini\n')
    phasefile.close()
    print('phasefile %s generated.' % phaseName)

def generateGraphfile(graphName, jobSize):
    '''
    generate the graph used in unstructured motif. Not useful now.
    graphName is the .mtx file name.
    '''
    import random
    randGraph = False
    tempname = 'graph_files/' + graphName
    graphfile = open(tempname, 'w')
    graphfile.write('%%MatrixMarket matrix coordinate pattern symmetric\n')
    core = int(jobSize * nodeInGroup * 2)
    link = core*(core-1)
    graphfile.write('%d %d %d\n' % (core, core, link))
    # core number starts from 1, not 0.
    if randGraph == False:
        for i in range(1, core+1):
            for j in range(1, core+1):
                if i != j:# avoid self communication.
                    graphfile.write('%d\t%d\n' % (i, j))
    else:
        pair = []
        for i in range(1, core+1):
            for j in range(1, core+1):
                if i != j:# avoid self communication.
                    pair.append((i,j))
        while(len(pair) != 0):
            selPair = random.choice(pair)
            graphfile.write('%d\t%d\n' % (selPair[0], selPair[1]))
            pair.remove(selPair)
    graphfile.close()
    print('graphfile %s generated.' % graphName)
    

def run(cmd):
    '''
    Function to run linux commands.
    '''
    #print(cmd)
    os.system(cmd)

def submit_job(options):
    options.outdir = "%s/%s/%s" %(options.main_sim_path, options.exp_folder, options.exp_name)
    #os.environ['SIMOUTPUT'] = folder
    execcommand  = "hostname\n"
    execcommand += "date\n"
    execcommand += 'module load anaconda\n'# this line is necessary to prevent library problem.
    execcommand += "source %s\n" %(options.env_script)
    execcommand += "export SIMOUTPUT=%s/\n" %(options.outdir)
    execcommand += "python run_DetailedNetworkSim.py --emberOut ember.out --alpha %.2f --routing %s --dflyShape %s --shuffle --schedPy sstInput/%s\n" %(options.alpha, options.routing, options.dflyShape, options.sstInputName)
    execcommand += "date\n"

    shfile = "%s/%s.sh" %(options.outdir, options.exp_name)
    outfile = "%s/%s.out" %(options.outdir, options.exp_name)

    #Check name only
    if options.check:
        print(options.exp_name)
    #Launch the experiment
    else:
        if os.path.exists(options.outdir) == 1:
            if options.force == 1:
                print("Clobbering %s... used -f flag" %(options.exp_name[:7]))
                run("rm -rf " + options.outdir)
            else:
                print("Experiment %s... exists. not submitting. use -f to force" %(options.exp_name[:7]))
                return 1
        run("mkdir -p " + options.outdir)

        shellfile = open(shfile, "w")
        shellfile.writelines(execcommand) # write() is enough.
        shellfile.close()

        cmd = "chmod +x %s" %(shfile)
        run(cmd)

        if qsub == False:
            cmd = "%s" % (shfile)
        else:
            cmd1 = 'qsub -q %s ' % (queue) if setQueue else 'qsub '
            cmd2 = '-l mem_free=%dG,s_vmem=%dG,h_vmem=%dG ' % (memory, memory, memory) if useMoreMemory else ''
            cmd = cmd1 + cmd2 + '-cwd -o %s -j y %s' % (outfile, shfile)
            # -j y: merge error to output. -S: specify the shell.
        run(cmd)
    return 0

if __name__ == '__main__':
    main()
