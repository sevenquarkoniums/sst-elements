#!/usr/bin/env python
'''
Created by  : Yijia Zhang
Description : Run a batch of sst jobs with NetworkSim

small machine:: 136=2*4*17 nodes, 2 cores per node.
large machine:: 272=2*8*17 nodes.

hybrid allocation only supporting 2 sizes of jobs.

run by:
./run.py 5 1 2 6 # mode hybrid.
./run.py 6 # mode baseline.

### TODO ###

### CANDO ###
find the best allocation.

### warning ###
!!! cannot change routing/shape before all program started the second sst.

machine size
::need to change snapshotParser_sched.py for different machine size. and pyfileTemplate.

loadfile
::sst-generated loadfile is abandoned, instead using myloadfile now. But the task-mapping is done on the old loadfile.

message size
::emberunstructured.cc modified p_size to 1000 to shorten alltoall simulation time. 100 won't work well, with output stall being 0.
::message size is changed in phasefiles.
'''
import sys
if sys.platform == 'win32':
    print('Do not run locally.\n')
    sys.exit(0)
#====================================
main_sim_path = "/mnt/nokrb/zhangyj/SST/scratch/src/sst-elements/src/sst/elements/scheduler/simulations"
env_script = "/mnt/nokrb/zhangyj/SST/exportSST.sh" # only modifys the environment variables.
qsub = False# whether qsub the program.
setQueue = False
if setQueue:
    queue = 'icsg.q' #bme.q, ece.q, me.q is great.
useMoreMemory = False
if useMoreMemory:
    memory = 4
#------------------------------------
useUnstrMotif = False# not recommended.

RouterInGroup = 4
groupNum = 17 
nodeOneRouter = 2
nodeInGroup = RouterInGroup * nodeOneRouter

mode = 'randomSized'# singleType, hybrid, baseline, randomSized.
applications = ['alltoall'] #['alltoall', 'bisection', 'mesh']
mappers = ['libtopomap'] # simple.
alphaRange = [4.0]#[0.5, 1.0, 2.0, 4.0]
messageIters = [2]#[2**x for x in range(4)]
messageSizes = [10**5]#[10**x for x in range(1,8)]

shuffle = True# shuffle the node list in myloadfile.

if mode == 'hybrid':
    sNum = int(sys.argv[1])
    sSize = int(sys.argv[2])
    lNum = int(sys.argv[3])
    lSize = int(sys.argv[4])

    hString = 'Hybrid_R%dG%d_%s_%d_%d_%d_%d' % (RouterInGroup, groupNum, applications[0], sNum, sSize, lNum, lSize)
    simfileName = hString + '.sim'
    graphfileNames = [hString + 'S.mtx', hString + 'L.mtx']
    phasefileNames = [hString + 'S.phase', hString + 'L.phase']
    
    iterRandom = 64
    iterNotRandom = 16
    allocStrategy = ['simple', 'spread', 'hybrid', 'random']#['simple', 'spread', 'hybrid', 'hybridRandom', 'random']
elif mode == 'baseline':# single job in an empty machine.
    sNum = 8 
    sSize = int(sys.argv[1])
    lNum = 0
    lSize = 2

    hString = 'Baseline_R%dG%d_%s_%d' % (RouterInGroup, groupNum, applications[0], sSize)# routing is included later.
    simfileName = hString + '.sim'
    graphfileNames = [hString + '.mtx']
    phasefileNames = [hString + '.phase']
    
    allocStrategy = ['spread']#['simple', 'spread', 'random']#['simple', 'simpleHeadEnd', 'spreadLimited']
    iterRandom = 1
    iterNotRandom = 1
elif mode == 'singleType':
    simfileName = 'alltoall_LN8.sim'
    graphfileNames = 'alltoall_LN8.mtx'
    phasefileNames = 'alltoall.phase'
elif mode == 'randomSized':
    sizeMax = 24 # possible largest number of nodes of one job.
    jobNum = 32
    hString = 'randomSized_%d_%d' % (jobNum, sizeMax)
    simfileName = '%s.sim' % hString
    phasefileName = '%s.phase' % hString 

#------------------------------------
# should use more decent code in the future.
ifChangeSnap = False# use True when shape/routing/useMyLoadfile changed.
routing = 'adaptive_local'#routing: minimal, valiant, adaptive_local.

if mode == 'hybrid' or mode == 'baseline':
    useMyLoadfile = True
elif mode == 'singleType' or mode == 'randomSized':
    useMyLoadfile = False

#====================================
shape = '%d:%d:%d:%d' % (nodeOneRouter, RouterInGroup, 1, groupNum)
    # hosts_per_router, routers_per_group, intergroup_per_router, num_groups.

import os, sys
from optparse import OptionParser
import os.path
import random

def main():

    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option("-c",  action='store_true', dest="check", help="Check the experiment file names.")
    parser.add_option("-f",  action='store_true', dest="force", help="Force the experiment, will clobber old results.") # overide old results
    parser.add_option("-e",  action='store', dest="exp_folder", help="Main experiment folder that holds all subfolders of the experiment.")
    # the -e para is overwrited in submit_job().
    (options, args) = parser.parse_args()

    if options.check == True:
        print("Action : Checking experiment file names")
    else:
        print("Action : Launching experiment")

    options.main_sim_path = main_sim_path
    options.env_script = env_script
    
    if ifChangeSnap == True:
        changeSnapSched(routing, shape, str(useMyLoadfile))

    if mode == 'baseline':
        generateSimfile(simfileName, graphfileNames , phasefileNames, 1000)
        generatePhasefile(graphfileNames[0], phasefileNames[0])
        generateGraphfile(graphfileNames[0], sSize)
        generatePyfile(simfileName, 'libtopomap', hString)
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
                            submit_job(options, strategy, messageIter, messageSize)
    elif mode == 'hybrid':
        generateSimfile(simfileName, graphfileNames , phasefileNames, 1000)
        for iphase, phase in enumerate(phasefileNames):
            generatePhasefile(graphfileNames[iphase], phasefileNames[iphase])
        generateGraphfile(graphfileNames[0], sSize)
        generateGraphfile(graphfileNames[1], lSize)
        for application in applications:
            for mapper in mappers:
                generatePyfile(simfileName, mapper, hString)
                for strategy in allocStrategy:
                    if strategy == 'random' or strategy == 'hybridRandom':
                        num_iters = iterRandom
                    else:
                        num_iters = iterNotRandom
                    for alpha in alphaRange:
                        for messageIter in messageIters:
                            for messageSize in messageSizes:
                                for iteration in range(num_iters):
                                    options.alpha = alpha
                                    options.application = application
                                    options.mapper = mapper
                                    options.iteration = iteration
                                    submit_job(options, strategy, messageIter, messageSize)
    elif mode == 'randomSized':
        generateSimfile(simfileName, 'empty' , phasefileName, 1000, sizeMax, jobNum)
        generatePhasefile('empty', phasefileName)
        for application in applications:
            for mapper in mappers:
                generatePyfile(simfileName, mapper, hString)
                options.application = application
                options.mapper = mapper
                submit_job(options)

def generateMyLoadfile(options, graphName, strategy, messageIter, messageSize):
    '''
    messageSize: only for alltoall motif.
    '''
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


def generatePyfile(simfileName, mapper, pyName):
    '''
    use a python file template to generate the required file.
    '''
    lines = open('pyfileTemplateR%dG%d.py' % (RouterInGroup, groupNum) ).read().splitlines()# template.
    wlines = []# making a copy and make change on that copy.
    for row in lines:
        if 'traceName' in row:# "traceName" : "jobtrace_files/alltoall_N8.sim",
            sim = row.split('\"')[3]
            sim = sim.split('/')[1]
            row = row.replace(sim, simfileName)
#        elif 'allocator' in row:# "allocator" : "simple",
#            currentAlloc = row.split('\"')[3]
#            if allocator == 'simple':
#                row = row.replace(currentAlloc, allocator)
#            elif allocator == 'spread':
#                row = row.replace(currentAlloc, 'simplespread')
#            elif allocator == 'random':
#                row = row.replace(currentAlloc, allocator)
        elif 'taskMapper' in row:# "taskMapper" : "topo",
            currentMapper = row.split('\"')[3]
            if mapper == 'simple':
                row = row.replace(currentMapper, mapper)
            elif mapper == 'libtopomap':
                row = row.replace(currentMapper, 'topo')
            elif mapper == 'random':
                row = row.replace(currentMapper, 'random')
        wlines.append(row)
#    pyfileName = '%s_%s_%s_N%d.py' % (allocator, mapper, application, N)# simple_libtopomap_alltoall_N8.py
    pyfileName = '%s.py' % (pyName)
    pyo = open(pyfileName,'w')
    pyo.write('\n'.join(wlines))
    pyo.close()
    print('%s generated.' % pyfileName)


def changeSnapSched(expectR, expectShape, expectMyload):
    '''
    change the parameters in snapshotParser_sched.py.
    '''
    snapold = open('snapshotParser_sched.py')
    lines = snapold.read().splitlines()
    wlines = []
    for row in lines:
        if 'routing =' in row:# routing = 'valiant'.
            currentR = row.split('\'')[1]
            row = row.replace(currentR, expectR)
        elif 'useMyLoadfile = ' in row:# useMyLoadfile = False# name: myloadfile.
            currentMyload = row.split('=')[1]
            currentMyload = currentMyload.split('#')[0]
            currentMyload = currentMyload[1:]
            row = row.replace(currentMyload, expectMyload)
        elif row.startswith('dragonPara'):# dragonPara = '2:4:1:17' # hosts_per_router, routers_per_group, intergroup_per_router, num_groups.
            currentShape = row.split('\'')[1]
            row = row.replace(currentShape, expectShape)
        
        wlines.append(row)
    snapold.close()
    snap = open('snapshotParser_sched.py','w')
    snap.write('\n'.join(wlines))
    snap.close()
    print('snapshotParser_sched.py modified.')
    
def generateSimfile(simName, graphName, phaseName, runtime, sizeMax=1, jobNum=1):
    '''
    generate the .sim files in the jobtrace_file folder.
    mode: 'randomSized' generate a list of random sized (node number) jobs.
        'twoSized' generate small/large jobs.
    runtime is an int in microseconds.
    In 'twoSized' mode, graphName and phaseName are lists.
    In 'randomSized' mode, graphName is ignored. phaseName and phasefile content are the same for all jobs.
    sizeMax is the max node number possible.
    jobNum is the number of jobs.
    '''
    import random
    tempname = 'jobtrace_files/' + simName
    simfile = open(tempname, 'w')
    if mode == 'baseline' or mode == 'hybrid':
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
    elif mode == 'randomSized':
        for ijob in range(jobNum):
            node = random.randint(1, sizeMax)
            print('jobSize: %d nodes' % node)
            core = node * 2
            arriveTime = ijob * 100 # can be changed into Poisson process.
            simLine = '%d %d %d -1 phase phase_files/%s\n' % (arriveTime, core, runtime, phaseName)
            simfile.write(simLine)

    simfile.close()
    print('%s generated.' % simName)

def generatePhasefile(graphName, phaseName):
    tempname = 'phase_files/' + phaseName
    phasefile = open(tempname, 'w')
    phasefile.write('Init\n')
    if useUnstrMotif == True:
        phasefile.write('Unstructured\tgraphfile=graph_files/%s\n' % graphName)
    else:
        phasefile.write('Alltoall\n')
    phasefile.write('Fini\n')
    phasefile.close()
    print('%s generated.' % phaseName)

def generateGraphfile(graphName, jobSize):
    '''
    generate the graph used in unstructured.
    graphName is the .mtx file name.
    '''
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
    print('%s generated.' % graphName)
    

def run(cmd):
    '''
    Function to run linux commands.
    '''
    #print(cmd)
    os.system(cmd)

def submit_job(options, strategy='empty', messageIter=1, messageSize=1):
    if mode == 'hybrid' or mode == 'baseline':
        exp_name = 'alpha%s_%s_%s_%s_%d_%d_iter%s' %(options.alpha, options.application, strategy, options.mapper, messageIter, messageSize, options.iteration)
        if routing == 'adaptive_local':
            options.exp_folder = '%s_%s' % (hString, 'adaptive')# overide the -e parameter.
        else:
            options.exp_folder = '%s_%s' % (hString, routing)# overide the -e parameter.
    elif mode == 'randomSized':
        exp_name = '%s_%s' %(options.application, options.mapper)
        options.exp_folder = '%s' % (hString)# overide the -e parameter.

    options.outdir = "%s/%s/%s" %(options.main_sim_path, options.exp_folder, exp_name)
    #os.environ['SIMOUTPUT'] = folder
    execcommand  = "hostname\n"
    execcommand += "date\n"
    execcommand += 'module load anaconda\n'# this line is necessary to prevent library problem.
    execcommand += "source %s\n" %(options.env_script)
    execcommand += "export SIMOUTPUT=%s/\n" %(options.outdir)
    if mode == 'hybrid' or mode == 'baseline':
        execcommand += "python run_DetailedNetworkSim.py --emberOut ember.out --alpha %s --schedPy ./%s.py\n" %(options.alpha, hString)
    elif mode == 'randomSized':
        execcommand += "python run_DetailedNetworkSim.py --emberOut ember.out --schedPy ./%s.py\n" %(hString)
    execcommand += "date\n"

    shfile = "%s/%s.sh" %(options.outdir, exp_name)
    outfile = "%s/%s.out" %(options.outdir, exp_name)

    #Check name only
    if options.check == True:
        print(options.outdir)
        print(execcommand)
        print(shfile)
        print(outfile)
        print
    #Launch the experiment
    else:
        if os.path.exists(options.outdir) == 1:
            if options.force == 1:
                print("Clobbering %s... used -f flag" %(exp_name))
                run("rm -rf " + options.outdir)
            else:
                print("Experiment %s exists... quitting. use -f to force" %(exp_name))
                sys.exit(1)
        run("mkdir -p " + options.outdir)
        if useMyLoadfile:
            generateMyLoadfile(options, graphfileNames, strategy, messageIter, messageSize)

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
#            cmd = ("qsub -q %s -l mem_free=%dG,s_vmem=%dG,h_vmem=%dG -cwd -S /bin/bash -o %s -j y %s" % (queue, memory, memory, memory, outfile, shfile)) 
            # -j y: merge error to output. -S: specify the shell.
        run(cmd)
        #run("%s" %(shfile))


if __name__ == '__main__':
    main()
