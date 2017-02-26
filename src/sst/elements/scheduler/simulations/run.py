#!/usr/bin/env python
'''
Created by  : Yijia Zhang
Description : Run a batch of sst jobs.

run by:
    ./run.py gen
    ./run.py run -f

### TODO ###

### CANDO ###

### warning ###

'''
import sys
if sys.platform == 'win32':
    print('Do not run locally.\n')
    sys.exit(0)
#====================================
#----- folder variables -----#
main_sim_path = "/mnt/nokrb/zhangyj/SST/scratch/src/sst-elements/src/sst/elements/scheduler/simulations"
env_script = "/mnt/nokrb/zhangyj/SST/exportSST.sh" # only modifys the environment variables.

#----- queue variables -----#
qsub = True# whether qsub the program.
setQueue = False
if setQueue:
    queue = 'icsg.q' #bme.q, ece.q, me.q is great.
useMoreMemory = False
if useMoreMemory:
    memory = 4

#----- simulation parameters -----#
mode = sys.argv[1]# gen, empty, run.
emberSimulation = True

groupNums = [17]
routersPerGroups = [4]
nodeOneRouters = [4]
alphas = [1]#[0.25, 0.5, 1, 2, 4]# print as %.2f number.
utilizations = [75]#[50, 75, 100]

allocations = ['random', 'dflyrdr', 'dflyrdg', 'dflyrrn', 'dflyrrr', 'dflyslurm', 'dflyhybrid']
mappers = ['topo'] # if want to change this, need to change the sst input file.
routings = ['adaptive_local']#['minimal', 'valiant', 'adaptive_local']
schedulers = ['easy']
applications = ['alltoall'] #['alltoall', 'bisection', 'mesh']
messageSizes = [10**5]#[10**x for x in range(1,8)]
messageIters = [2]#[2**x for x in range(4)]

traceModes = ['corner']
sizeMax = 32 # possible largest number of nodes of one job.
expIters = 1

if mode == 'baseline':# single job in an empty machine.
    sNum = 8
    sSize = int(sys.argv[1])
    lNum = 0
    lSize = 2

    hString = 'Baseline_R%dG%d_%s_%d' % (routersPerGroup, groupNum, applications[0], sSize)# routing is included later.
    pyfileName = hString + '.py'
    simfileName = hString + '.sim'
    graphfileNames = [hString + '.mtx']
    phasefileNames = [hString + '.phase']

    allocStrategy = ['spread']#['simple', 'spread', 'random']#['simple', 'simpleHeadEnd', 'spreadLimited']
    iterRandom = 1
    iterNotRandom = 1


#====================================

useUnstrMotif = False# not recommended.

#shuffle = True# shuffle the node list in myloadfile.

import os, sys
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

    if mode == 'baseline':
        generateSimfile(simfileName, graphfileNames , phasefileNames, 1000)
        generatePhasefile(graphfileNames[0], phasefileNames[0])
        generateGraphfile(graphfileNames[0], sSize)
        generatePyfile(simfileName, 'libtopomap', pyfileName, dflyArgv, 'simple')
        for strategy in allocStrategy:
            if strategy == 'random' or strategy == 'spreadRandom':
                num_iters = iterRandom
            else:
                num_iters = iterNotRandom
            for alpha in alphaRange:
                for messageIter in messageIters:
                    for messageSize in messageSizes:
                        for iteration in range(num_iters):
                            options.alpha = alpha
                            options.application = applications[0]
                            options.mapper = 'libtopomap'
                            options.iteration = iteration
                            options.routing = 'minimal'
                            submit_job(options, strategy, messageIter, messageSize)

    elif mode == 'gen':
        print('to do')

    elif mode == 'run':
        options.exp_folder = 'hybrid'
        for groupNum in groupNums:
            for routersPerGroup in routersPerGroups:
                for nodeOneRouter in nodeOneRouters:
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
                                    if application == 'alltoall':
                                        phasefileName = '%s_mesSize%d_mesIter%d.phase' % (application, messageSize, messageIter)
                                        generatePhasefile(phasefileName, messageSize, messageIter)
                                    for traceMode in traceModes:
                                        traceNums = 8 if traceMode == 'corner' else 100
                                        for traceNum in range(1, traceNums + 1):
                                            # trace numbers start from 1.
                                            name1 = 'G%dR%dN%d_uti%d_%s_mesSize%d_mesIter%d_%s_%d' % (groupNum, routersPerGroup, nodeOneRouter, 
                                                    utilization, application, messageSize, messageIter, traceMode, traceNum)
                                            simfileName = name1 + '.sim'
                                            generateSimfile(simfileName, nodesToAlloc, nodeOneRouter, routersPerGroup, 'corner', traceNum, 
                                                    graphName='empty', phaseName=phasefileName, runtime=1000, sizeMax=sizeMax)
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

    else:
        print('mode not valid')

#----- main end -----#

def generateMyLoadfile(options, graphName, strategy, messageIter, messageSize):
    '''
    this function is obsolete now.
    messageSize: only for alltoall motif.
    '''
    import random
    # set the number of nodes needed by each job.
    jobs = []
    # the following is for sNum + lNum hybrid job.
    for i in range(sNum):
        jobs.append(int(nodeInGroup * sSize))
    for i in range(lNum):
        jobs.append(int(nodeInGroup * lSize))
    
    # stores the allocation method. 1st for job number. 2nd for node numbers of each job.
    allocation = [[] for i in range(len(jobs))]
    # 2-d list shows available nodes. 1st for group, 2st for node.
    freeNode = [[] for i in range(groupNum)]
    nodeNum = nodeInGroup * groupNum
    for inode in range(nodeNum):
        freeNode[int(inode/nodeInGroup)].append(inode)
    
    if strategy == 'simple':
        currentGroup = 0
        for ijob, job in enumerate(jobs):
            while(job != 0):
                if len(freeNode[currentGroup]) != 0:
                    allocNode = freeNode[currentGroup][0]
                    freeNode[currentGroup].remove(allocNode)
                else:
                    currentGroup += 1
                    if currentGroup == groupNum:
                        currentGroup = 0
                    continue
                allocation[ijob].append(allocNode)
                job -= 1
    elif strategy == 'simpleHeadEnd':# choose the head then the end when allocating in one group.
        currentGroup = 0
        eta = 0
        for ijob, job in enumerate(jobs):
            while(job != 0):
                if len(freeNode[currentGroup]) != 0:
                    allocNode = freeNode[currentGroup][eta]
                    freeNode[currentGroup].remove(allocNode)
                    if eta == 0:
                        eta = -1
                    elif eta == -1:
                        eta = 0
                else:
                    currentGroup += 1
                    if currentGroup == groupNum:
                        currentGroup = 0
                    continue
                allocation[ijob].append(allocNode)
                job -= 1
    elif strategy == 'simpleRandom':# random choose a node when allocating in one group.
        currentGroup = 0
        for ijob, job in enumerate(jobs):
            while(job != 0):
                if len(freeNode[currentGroup]) != 0:
                    allocNode = random.choice(freeNode[currentGroup])
                    freeNode[currentGroup].remove(allocNode)
                else:
                    currentGroup += 1
                    if currentGroup == groupNum:
                        currentGroup = 0
                    continue
                allocation[ijob].append(allocNode)
                job -= 1
    elif strategy == 'spreadLimited':# only works for a single job. spread but limited in the condensed groups.
        currentGroup = 0
        for ijob, job in enumerate(jobs):
            while(job != 0):
                if len(freeNode[currentGroup]) != 0:
                    allocNode = freeNode[currentGroup][0]
                    #allocNode = random.choice(freeNode[currentGroup])# randomness in selection.
                    freeNode[currentGroup].remove(allocNode)
                else:
                    currentGroup += 1
                    if currentGroup == groupNum:
                        currentGroup = 0
                    continue
                allocation[ijob].append(allocNode)
                currentGroup += 1# change group when successfully allocate a job.
                if currentGroup == sSize:
                    currentGroup = 0
                job -= 1
    elif strategy == 'localSpread':# select one node and jump to next router in the same group.
        currentGroup = 0
        currentNode = 0
        for ijob, job in enumerate(jobs):
            while(job != 0):
                if len(freeNode[currentGroup]) != 0:
                    allocNode = freeNode[currentGroup][currentNode]
                    freeNode[currentGroup].remove(allocNode)
                    currentNode += 1
                    if currentNode >= freeNode[currentGroup]:
                        currentNode = 0
                else:
                    currentGroup += 1
                    if currentGroup == groupNum:
                        currentGroup = 0
                    continue
                allocation[ijob].append(allocNode)
                job -= 1
    elif strategy == 'spread':
        currentGroup = 0
        for ijob, job in enumerate(jobs):
            while(job != 0):
                if len(freeNode[currentGroup]) != 0:
                    allocNode = freeNode[currentGroup][0]# add randomness in this line.
                    freeNode[currentGroup].remove(allocNode)
                else:
                    currentGroup += 1
                    if currentGroup == groupNum:
                        currentGroup = 0
                    continue
                allocation[ijob].append(allocNode)
                currentGroup += 1# change group when successfully allocate a job.
                if currentGroup == groupNum:
                    currentGroup = 0
                job -= 1
    elif strategy == 'nodeSpread':# allocate all 2 nodes in a router then change to next group.
        currentGroup = 0
        for ijob, job in enumerate(jobs):
            while(job != 0):
                if len(freeNode[currentGroup]) != 0:
                    allocNode = freeNode[currentGroup][0]# add randomness in this line.
                    freeNode[currentGroup].remove(allocNode)
                else:
                    currentGroup += 1
                    if currentGroup == groupNum:
                        currentGroup = 0
                    continue
                allocation[ijob].append(allocNode)
                if allocNode % 2 == 1:
                    currentGroup += 1# change group when an odd number node is allocated.
                if currentGroup == groupNum:
                    currentGroup = 0
                job -= 1
    elif strategy == 'spreadRandom':
        currentGroup = 0
        for ijob, job in enumerate(jobs):
            while(job != 0):
                if len(freeNode[currentGroup]) != 0:
                    allocNode = random.choice(freeNode[currentGroup])
                    freeNode[currentGroup].remove(allocNode)
                else:
                    currentGroup += 1
                    if currentGroup == groupNum:
                        currentGroup = 0
                    continue
                allocation[ijob].append(allocNode)
                currentGroup += 1# change group when successfully allocate a job.
                if currentGroup == groupNum:
                    currentGroup = 0
                job -= 1
    elif strategy == 'hybrid':
        # add the grouped ones first serially. mark the nodes as allocated.
        for ialloc in range(sNum):
            allocation[ialloc] = list(range(int(nodeInGroup * sSize * ialloc), int(nodeInGroup * sSize * (ialloc+1))))
            # this works only if no small job occupys part of a group.
            freeNode[int(ialloc * sSize)] = []

        currentGroup = 0
        for ijob, job in enumerate(jobs):
            # jump the allocated jobs.
            if ijob < sNum:
                continue

            while(job != 0):
                if len(freeNode[currentGroup]) != 0:
                    allocNode = freeNode[currentGroup][0]# add randomness in this line.
                    freeNode[currentGroup].remove(allocNode)
                else:
                    currentGroup += 1
                    if currentGroup == groupNum:
                        currentGroup = 0
                    continue
                allocation[ijob].append(allocNode)
                currentGroup += 1# change group when successfully allocate a job.
                if currentGroup == groupNum:
                    currentGroup = 0
                job -= 1
    
    elif strategy == 'hybridRandom':
        # add the grouped ones first serially. mark the nodes as allocated.
        for ialloc in range(sNum):
            allocation[ialloc] = list(range(int(nodeInGroup * sSize * ialloc), int(nodeInGroup * sSize * (ialloc+1))))
            # this works only if no small job occupys part of a group.
            freeNode[int(ialloc * sSize)] = []

        currentGroup = 0
        for ijob, job in enumerate(jobs):
            # jump the allocated jobs.
            if ijob < sNum:
                continue

            while(job != 0):
                if len(freeNode[currentGroup]) != 0:
                    allocNode = random.choice(freeNode[currentGroup])
                    freeNode[currentGroup].remove(allocNode)
                else:
                    currentGroup += 1
                    if currentGroup == groupNum:
                        currentGroup = 0
                    continue
                allocation[ijob].append(allocNode)
                currentGroup += 1# change group when successfully allocate a job.
                if currentGroup == groupNum:
                    currentGroup = 0
                job -= 1
    elif strategy == 'random':
        freeGroup = [x for x in range(groupNum)]
        for ijob, job in enumerate(jobs):
            while(job != 0):
                currentGroup = random.choice(freeGroup)
                if len(freeNode[currentGroup]) != 0:
                    allocNode = random.choice(freeNode[currentGroup])
                    freeNode[currentGroup].remove(allocNode)
                else:
                    freeGroup.remove(currentGroup)
                    continue
                allocation[ijob].append(allocNode)
                job -= 1

    if shuffle:
        for job in allocation:
            random.shuffle(job)

    # parameters for this part are in ember.cc.
    fo = open(options.outdir + '/myloadfile','w')
    for ijob, jobAlloc in enumerate(allocation):
        fo.write('[JOB_ID] %d\n' % ijob)
        fo.write('\n')
        fo.write('[NID_LIST] ')
        fo.write(','.join(str(x) for x in jobAlloc))
        fo.write('\n')
        fo.write('[MOTIF] Init\n')
        if options.application == 'mesh':
            fo.write('[MOTIF] Halo3D iterations=%d doreduce=0 pex=4 pey=4 pez=4\n' % messageIter)# number should change.
        elif options.application == 'alltoall':
            if ijob < sNum:# for small job.
                if useUnstrMotif == True:
                    fo.write('[MOTIF] Unstructured iterations=%d\tgraphfile=graph_files/%s\n' % (messageIter, graphName[0]) )
                else:
                    fo.write('[MOTIF] Alltoall iterations=%d\tbytes=%d\n' % (messageIter, messageSize) )
            else:# for large jobs.
                if useUnstrMotif == True:
                    fo.write('[MOTIF] Unstructured iterations=%d\tgraphfile=graph_files/%s\n' % (messageIter, graphName[1]) )
                else:
                    fo.write('[MOTIF] Alltoall iterations=%d\tbytes=%d\n' % (messageIter, messageSize) )
        fo.write('[MOTIF] Fini\n')
        fo.write('\n')
    fo.close()


def generatePyfile(sstInputName, simfileName, application, mapper, dflyArgv, allocator):
    '''
    use a python file template to generate the required file.
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

def generateSimfile(simName, nodesToAlloc, nodeOneRouter, routersPerGroup, traceMode, traceNum, graphName, phaseName, runtime, sizeMax):
    '''
    generate the .sim files in the jobtrace_file folder.

    traceMode = 'corner' generate corner cases.
    runtime is an int in microseconds setting the assumed running time of a job.
    sizeMax is the max node number possible in random mode.
    '''
    import random
    tempname = 'jobtrace_files/' + simName
    simfile = open(tempname, 'w')
    if traceMode == 'baseline':
        # for small job.
        score = int(sSize * nodeInGroup * 2) # small_core.
        if useUnstrMotif == True:
            simLine = '0 %d %d -1 comm\tgraph_files/%s\tphase phase_files/%s\n' % (score, runtime, graphName[0], phaseName[0])
        else:
            simLine = '0 %d %d -1 phase phase_files/%s\n' % (score, runtime, phaseName[0])
        for iN in range(sNum):
            simfile.write(simLine)
        # for large jobs.
        lcore = int(lSize * nodeInGroup * 2)
        if lNum != 0:
            if useUnstrMotif == True:
                simLine = '0 %d %d -1 comm\tgraph_files/%s\tphase phase_files/%s\n' % (lcore, runtime, graphName[1], phaseName[1])
            else:
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (lcore, runtime, phaseName[1])
        for iN in range(lNum):
            simfile.write(simLine)

    elif traceMode == 'corner':
        # some corner cases.
        if traceNum == 1:
            node = 2
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 2:
            node = nodeOneRouter
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 3:
            node = nodeOneRouter * routersPerGroup
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 4:
            node = int(nodesToAlloc / 4) # the case that all jobs are large.
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 5:
            node = nodeOneRouter
            core = node * 2
            jobNum = int( ( nodesToAlloc - int(nodesToAlloc / 4) ) / 2 )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)

            node = int(nodesToAlloc / 4)
            core = node * 2
            simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
            simfile.write(simLine)
        elif traceNum == 6:
            node = nodeOneRouter
            core = node * 2
            simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
            simfile.write(simLine)

            node = int(nodesToAlloc / 4)
            core = node * 2
            jobNum = int( ( nodesToAlloc - nodeOneRouter ) / node )
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 7:
            node = nodeOneRouter + 1
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)
        elif traceNum == 8:
            node = nodeOneRouter * routersPerGroup + 1
            core = node * 2
            jobNum = int(nodesToAlloc / node)
            for ijob in range(jobNum):
                simLine = '0 %d %d -1 phase phase_files/%s\n' % (core, runtime, phaseName)
                simfile.write(simLine)

    elif traceMode == 'random':
        freeNode = int(nodeInGroup * groupNum * utilization/100)
        while freeNode != 0:
            node = random.randint(1, sizeMax)
            if node <= freeNode:
                # make a new job.
                freeNode = freeNode - node
                print('jobSize: %d nodes' % node)
                core = node * 2
                arriveTime = 0
                simLine = '%d %d %d -1 phase phase_files/%s\n' % (arriveTime, core, runtime, phaseName)
                simfile.write(simLine)
            else:
                # make all the freeNode to be a job.
                node = freeNode
                freeNode = 0
                print('jobSize: %d nodes' % node)
                core = node * 2
                arriveTime = 0
                simLine = '%d %d %d -1 phase phase_files/%s\n' % (arriveTime, core, runtime, phaseName)
                simfile.write(simLine)

    simfile.close()
    print('tracefile %s generated.' % simName)

def generatePhasefile(phaseName, messageSize, messageIter, graphName='empty'):
    tempname = 'phase_files/' + phaseName
    phasefile = open(tempname, 'w')
    phasefile.write('Init\n')
    if useUnstrMotif == True:
        phasefile.write('Unstructured\tgraphfile=graph_files/%s\n' % graphName)
    else:
        phasefile.write('Alltoall    iterations=%d    bytes=%d\n' % (messageIter, messageSize) )
    phasefile.write('Fini\n')
    phasefile.close()
    print('phasefile %s generated.' % phaseName)

def generateGraphfile(graphName, jobSize):
    '''
    generate the graph used in unstructured.
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
        print(options.outdir)
        print(execcommand)
        print(shfile)
        print(outfile)
        print
    #Launch the experiment
    else:
        if os.path.exists(options.outdir) == 1:
            if options.force == 1:
                print("Clobbering %s... used -f flag" %(options.exp_name[:7]))
                run("rm -rf " + options.outdir)
            else:
                print("Experiment %s... exists. quitting. use -f to force" %(options.exp_name[:7]))
                sys.exit(1)
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

if __name__ == '__main__':
    main()
