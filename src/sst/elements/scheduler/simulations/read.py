#!/usr/bin/env python
"""
@author: Yijia Zhang

read baseline and hybrid simulation results and process them.
used to read the 128 shuffle and find out how many shuffle is good enough and showing a normal distribution.

run by:
./read.py empty
./read.py analyzeEmpty
./read.py hybrid
./read.py draw

### TODO ###


### warning ###


"""
import sys
#=========================
mode = sys.argv[1]

#=========================
import datetime
now = datetime.datetime.now()

import numpy as np
import pandas as pd
if sys.platform == 'win32':
    sys.path.insert(0, 'C:/Programming/monitoring')
else:
    sys.path.insert(0, '/mnt/nokrb/zhangyj/monitoring')
import tools

if mode == 'hybrid':
    dfEmpty = pd.read_csv('empty.csv')

def main():
    if mode == 'hybrid':
        df = inspect('hybrid', mode)
        df.to_csv('hybrid.csv', index=False)

    elif mode == 'empty':
        df = inspect('empty', mode)
        df.to_csv('emptyRaw.csv', index=False)

    elif mode == 'analyzeEmpty':
        df = pd.read_csv('emptyRaw.csv')
        dfMin = emptyMin(df)
        dfMin.to_csv('empty.csv', index=False)

    elif mode == 'readSize':
        df = inspect('hybrid', mode)
        outname = 'allsize.txt'
        out = open('%s' % outname, 'w')
        for iSize in df:
            out.write('%d\n' % iSize)
        out.close()

    elif mode == 'draw':
        df = pd.read_csv('hybrid.csv')
        draw(df, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=2, 
                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)

    #readBaseline('Baseline_R4G17')
    #bestBase('Baseline_R4G17')
    #readHybrid('Hybrid_R4G17')
    #bestAlloc('Hybrid_R4G17')

    #fileIterSize('sizeIter')
    #fileUncertainty('iterUncertainty')

    # generate the files for matlab 3d ploting.
    #usefulCol = ['messageIter','messageSize','time(us)']
    #for selAlpha in [0.5]:#alphaRange:
    #    dfMatlab = df[df['alpha']==selAlpha].loc[:, usefulCol]
    #    dfMatlab.to_csv('%s/%s_matlab_%.1f.csv' % (mainFolderName, folder, selAlpha), index=False)
    print('finished in %d seconds.' % (datetime.datetime.now()-now).seconds)

def draw(df, groupNum, routersPerGroup, nodesPerRouter, utilization, application, messageSize, messageIter, traceMode, scheduler, routing, alpha):
    import matplotlib.pyplot as plt
    dfThis = df[
                (df['groupNum']==groupNum)
                & (df['routersPerGroup']==routersPerGroup)
                & (df['nodesPerRouter']==nodesPerRouter)
                & (df['utilization']==utilization)
                & (df['application']==application)
                & (df['messageSize']==messageSize)
                & (df['messageIter']==messageIter)
                & (df['traceMode']==traceMode)
                & (df['scheduler']==scheduler)
                & (df['routing']==routing)
                & (df['alpha']==alpha)
                ]
    allocations = set(dfThis['allocation'])
    traceNums = set(dfThis['traceNum'])

    # get the ANL for every repeated case.
    dfAvg = pd.DataFrame(columns=['groupNum','routersPerGroup','nodesPerRouter','utilization','application','messageSize','messageIter',
        'traceMode','traceNum','allocation','taskmapping','scheduler','routing','alpha','expIter','avg.ANL'])
    for traceNum in traceNums:
        for allocation in allocations:
            dfOneCase = dfThis[
                                (dfThis['traceNum']==traceNum)
                                & (dfThis['allocation']==allocation)
                                ]
            avg = dfOneCase['Avg.Norm.Latency'].mean()
            dfAvg.loc[len(dfAvg),:] = [groupNum,routersPerGroup,nodesPerRouter,utilization,application,messageSize,messageIter,
                    traceMode,traceNum,allocation,'all',scheduler,routing,alpha,'all',avg]

    dfAvg.to_csv('test.csv',index=False)
    dfAvg['avg.ANL'].plot(kind='bar',title='title',figsize=(20,15),legend=True)
    plt.savefig('test.png')

def emptyMin(df):
    dfMin = pd.DataFrame(columns=['groupNum','routersPerGroup','nodesPerRouter','utilization','application','messageSize','messageIter',
        'traceMode','traceNum','allocation','taskmapping','scheduler','routing','alpha','expIter','time(us)'])
    groupNums = set(df['groupNum'])
    routersPerGroups = set(df['routersPerGroup'])
    nodesPerRouters = set(df['nodesPerRouter'])
    applications = set(df['application'])
    messageSizes = set(df['messageSize'])
    messageIters = set(df['messageIter'])
    sizes = set(df['traceNum'])
    routings = set(df['routing'])
    alphas = set(df['alpha'])
    for groupNum in groupNums:
        for routersPerGroup in routersPerGroups:
            for nodesPerRouter in nodesPerRouters:
                for application in applications:
                    for messageSize in messageSizes:
                        for messageIter in messageIters:
                            for size in sizes:
                                for routing in routings:
                                    for alpha in alphas:
                                        dfOneCase = df[
                                                        (df['groupNum']==groupNum)
                                                        & (df['routersPerGroup']==routersPerGroup)
                                                        & (df['nodesPerRouter']==nodesPerRouter)
                                                        & (df['application']==application)
                                                        & (df['messageSize']==messageSize)
                                                        & (df['messageIter']==messageIter)
                                                        & (df['traceNum']==size)
                                                        & (df['routing']==routing)
                                                        & (df['alpha']==alpha)
                                                        ]
                                        timeMin = dfOneCase['time(us)'].min()
                                        dfMin.loc[len(dfMin),:] = [groupNum,routersPerGroup,nodesPerRouter,'all',application,messageSize,messageIter,
                                                'analyzeEmpty',size,'all','all','all',routing,alpha,'all',timeMin]
    return dfMin

def inspect(path, mode):
    '''
    get a table with results from all experiments.
    '''
    import pandas as pd
    print('reading %s...' % path)
    fileList = tools.getfiles(path)
    if mode == 'hybrid':
        df = pd.DataFrame(columns=['groupNum','routersPerGroup','nodesPerRouter','utilization','application','messageSize','messageIter',
            'traceMode','traceNum','allocation','taskmapping','scheduler','routing','alpha','expIter','Avg.Norm.Latency'])
    elif mode == 'empty':
        df = pd.DataFrame(columns=['groupNum','routersPerGroup','nodesPerRouter','utilization','application','messageSize','messageIter',
            'traceMode','traceNum','allocation','taskmapping','scheduler','routing','alpha','expIter','time(us)'])
    elif mode == 'readSize':
        df = set()

    for file in fileList:
        split = file.split('\\') if sys.platform == 'win32' else file.split('/')
        fname = split[-1]
        if fname == 'ember.out':
            para = split[-2]
            paraSplit = para.split('_')
            # exp info.
            machine = paraSplit[0]
            groupNum = int(machine.split('G')[1].split('R')[0])
            routersPerGroup = int(machine.split('R')[1].split('N')[0])
            nodesPerRouter = int(machine.split('N')[1])
            utilization = int(paraSplit[1].split('uti')[1])
            application = paraSplit[2]
            messageSize = int(paraSplit[3].split('mesSize')[1])
            messageIter = int(paraSplit[4].split('mesIter')[1])
            traceMode = paraSplit[5]
            traceNum = int(paraSplit[6])
            allocation = paraSplit[7]
            taskmapping = paraSplit[8]
            scheduler = paraSplit[9]
            routing = paraSplit[10]
            alpha = float(paraSplit[11].split('alpha')[1])
            expIter = int(paraSplit[12].split('expIter')[1])
            # read file.
            if mode == 'empty':
                (time, find) = read(file, 'last')
            elif mode == 'hybrid':
                parameters = {}
                parameters['groupNum'] = groupNum
                parameters['routersPerGroup'] = routersPerGroup
                parameters['nodesPerRouter'] = nodesPerRouter
                parameters['application'] = application
                parameters['messageSize'] = messageSize
                parameters['messageIter'] = messageIter
                parameters['routing'] = routing
                parameters['alpha'] = alpha
                (time, find) = read(file, 'ANL', parameters)
            elif mode == 'readSize':
                (oneFileSet, find) = read(file, 'readSize')

            if find == 1:# if find == 0 so simulation didn't complete, no records in the df.
                if mode == 'hybrid' or mode == 'empty':
                    df.loc[len(df),:] = [groupNum,routersPerGroup,nodesPerRouter,utilization,application,messageSize,messageIter,
                            traceMode,traceNum,allocation,taskmapping,scheduler,routing,alpha,expIter,time]
                elif mode == 'readSize':
                    for iSize in oneFileSet:
                        df.add(iSize)
            elif find == 0:
                print('incomplete file: %s' % para)
    return df

def read(file, readmode, parameters=0):
    '''
    read the finish time of one ember.out file.
    find: the finish line exists.
    '''
    infile = open(file, 'r')
    find = 0

    if readmode == 'last':# the finish time of the last job.
        for line in infile:
            if line.startswith('Job Finished:'):
                string = line.split(':')[4].split(' ')# 32101 us
                number = float(string[0])
                unit   = string[1].split('\n')[0]
                time = convertToMicro(number, unit)
            if line.startswith('Simulation is complete'):# make sure the simulation is complete.
                find = 1
        if find == 0:# no this line.
            time = 0

    elif readmode == 'readSize':
        sizes = set()
        for line in infile:
            if line.startswith('Job Finished:'):
                size = int( line.split(':')[3].split(' ')[0] )
                sizes.add(size)
            if line.startswith('Simulation is complete'):# make sure the simulation is complete.
                find = 1
        time = sizes# to return the set of jobsizes.

    elif readmode == 'complete':# the simulation time.
        for line in infile:
            if line.startswith('Simulation is complete'):
                find = 1
                string = line.split(':')[1].split(' ')
                number = float(string[1])
                unit   = string[2].split('\n')[0]
                time = convertToMicro(number, unit)
        if find == 0:# no this line.
            time = 0

    elif readmode == 'sumAll':
        times = []
        for line in infile:
            if line.startswith('Job Finished:'):# Job Finished: JobNum:0 Time:32101 us.
                JobNum = int(line.split(':')[2].split(' ')[0])
                string = line.split(':')[3].split(' ')# 32101 us
                number = float(string[0])
                unit   = string[1].split('\n')[0]
                oneTime = convertToMicro(number, unit)
                times.append(oneTime)
            if line.startswith('Simulation is complete'):# make sure the simulation is complete.
                find = 1
        if find == 0:# no this line.
            time = 0
        else:
            time = sum(times)

    elif readmode == 'ANL':
        NL = []
        for line in infile:
            if line.startswith('Job Finished:'):# Job Finished: JobNum:2 NodeNum:99 Time:303478 us
                size = int(line.split(':')[3].split(' ')[0])# 99
                string = line.split(':')[4].split(' ')# [303478, 'us\n']
                number = float(string[0])
                unit   = string[1].split('\n')[0]
                oneTime = convertToMicro(number, unit)
                emptyTime = dfEmpty[
                                    (dfEmpty['groupNum']==parameters['groupNum'])
                                    & (dfEmpty['nodesPerRouter']==parameters['nodesPerRouter'])
                                    & (dfEmpty['routersPerGroup']==parameters['routersPerGroup'])
                                    & (dfEmpty['application']==parameters['application'])
                                    & (dfEmpty['messageSize']==parameters['messageSize'])
                                    & (dfEmpty['messageIter']==parameters['messageIter'])
                                    & (dfEmpty['traceNum']==size)
                                    & (dfEmpty['routing']==parameters['routing'])
                                    & (dfEmpty['alpha']==parameters['alpha'])
                                    ].iloc[0]['time(us)']
                normalizedTime = oneTime / emptyTime
                NL.append(normalizedTime)
            if line.startswith('Simulation is complete'):# make sure the simulation is complete.
                find = 1
        if find == 0:# no this line.
            time = 0
        else:
            ANL = sum(NL) / len(NL)
            time = ANL
    infile.close()
    return (time, find)

def convertToMicro(number, unit):
    '''
    Converts the units for the time info to microseconds(us).
    '''
    if (unit == 'Ks'):
        convertedNum = number*1000000000
    elif (unit == 's'):
        convertedNum = number*1000000
    elif (unit == 'ms'):
        convertedNum = number*1000
    elif (unit == 'us'):
        convertedNum = number
    elif (unit == 'ns'):
        convertedNum = float(number/1000)
    else:
        print("ERROR: Valid time units: [Ks | s | ms | us | ns]")

    return (convertedNum)

def mean_confidence_interval(data, confidence=0.95):
    import scipy.stats
    a = 1.0*np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1+confidence)/2., n-1)
    return m, m-h, m+h
    
def checkUncertainty(mode, df, alloc, iteration, outdf, verb, alpha=0.95):
    '''
    # get avg. and estimate the relative error of avg.
    '''
    import math
    import scipy.stats
    dfPart = df[df['expIter']<iteration]
    dfPart = dfPart[dfPart['alloc']==alloc]
    if len(dfPart) != 0:
        if mode == 'traditional':# traditional way.
            avg = dfPart['time(us)'].mean()
            error_avg = dfPart['time(us)'].std()/math.sqrt(len(dfPart['time(us)']))/avg * 100
            outdf.loc[len(outdf), :] = [iteration, '%.1f%%' % error_avg]
            if verb:
                print('traditional estimation. avg:%.0f, relative error of avg:%.1f%%' %(avg, error_avg) )
        elif mode == 'wilson':
            # Wilson interval.
            mean, lower, upper = mean_confidence_interval(dfPart['time(us)'], alpha)
            errorUp = (upper/mean-1)*100
            if verb:
                print('Wilson confidence interval. avg:%.0f, relative upper error of avg:%.1f%%' %(mean, errorUp) )
        elif mode == 'bayesian':
            # Bayesian interval.
            (mean_cntr, var_cntr, std_cntr) = scipy.stats.bayes_mvs(dfPart['time(us)'], alpha)
            errorUp = (mean_cntr[1][1]/mean_cntr[0]-1)*100
            errorDown = (-mean_cntr[1][0]/mean_cntr[0]+1)*100
            if verb:
                print('Bayesian confidence interval. avg:%.0f, relative upper error of avg:%.1f%%, relative lower error of avg:%.1f%%' %(mean_cntr[0], errorUp, errorDown) )
    
def listUncertainty(mainFolderName, df):
    for alloc in ['simple','spread','random']:
        uncertainty = pd.DataFrame(columns=['iteration','uncertainty'])
        for iteration in [2**x for x in range(1, 8)]:
            checkUncertainty('traditional', df, alloc, iteration, uncertainty, False)
        if len(uncertainty) != 0:
            uncertainty.to_csv('%s/%s_%s_uncertainty.csv' % (mainFolderName, folder, alloc), index=False)

def fileUncertainty(mainFolderName):
    '''
    do read and list uncertainty for a file.
    '''
    df = inspect('%s/%s' % (mainFolderName, folder) )
    df.to_csv('%s/%s.csv' % (mainFolderName, folder), index=False)
    #df = pd.read_csv('%s/%s.csv' % (mainFolderName, folder) )
    listUncertainty(df)

def matrixIterSize(mainFolderName, df, mode, alpha=4.0):
    '''
    pivot the df into a 2d matrix, and output the .csv file.
    predict the time from messageSize=10^5, messageIter=8. And find the maximum deviation from the prediction.
    '''
    #from sklearn.linear_model import LinearRegression as linearReg
    #import numpy as np
    #dfPart = df[df['alpha']==alpha]
    ## select linear zone.
    #if mode == 'sizeIter':# count both the uncertainty from messageSize and messageIter.
    #    dfPart = dfPart[dfPart['messageSize']>=10**5]
    #elif mode == 'iterOnly':
    #    dfPart = dfPart[dfPart['messageSize']==10**5]

    # linear regression of logarithmic value. Abandoned.
    #x = dfPart[['messageSize','messageIter']].values.astype('float')
    #y = dfPart['time(us)'].values.astype('float')
    #logx = np.log(x)
    #logy = np.log(y)
#    print(logx)
#    print(logy)
    #clf = linearReg()
    #clf.fit(logx,logy)
    #print('coef:')
    #print(clf.coef_)
    #print('r-score:')
    #print(clf.score(logx, logy))
    #errRelative = np.exp(clf.predict(logx)) / y - 1
    
    # just get the avg of time-divided as the standard point to make predict.
    #time = dfPart['time(us)'].values.astype('float')
    #mS = dfPart['messageSize'].values
    #mI = dfPart['messageIter'].values
    #divide = time/mS/mI
    #standardPoint = np.mean(divide)
    #errRelative = time/(standardPoint*mS*mI)-1
    #stdErrRelative = np.std((errRelative))
    #print('standard point:')
    #print(standardPoint)
    ##print('relative error:')
    ##print(errRelative)
    #print('std of relative error:')
    #print(stdErrRelative)

    import numpy as np
    # pivot table.
    pdpiv = pd.pivot_table(df, values='time(us)', index=['alpha','messageIter'], columns=['messageSize'], aggfunc=np.sum)
    pdpiv.to_csv('%s/%s_pivot.csv' % (mainFolderName, folder) )

    sizeStand = 10**5
    iterStand = 2
    alphas = list(set(df['alpha']))
    for a in alphas:
        print('alpha: %.1f' % a)
        standardPoint = pdpiv.loc[(a, iterStand), sizeStand]
        devia = pdpiv.loc[a, :].copy()
        for col in devia.columns:
            devia.loc[:, col] = devia.loc[:, col]/standardPoint*sizeStand/col
        for row in devia.index:
            devia.loc[row, :] = devia.loc[row, :]/row*iterStand
        devia = devia - 1
        devia.to_csv('%s/%s_alpha%s_devia.csv' % (mainFolderName, folder, str(a)), index=False)
        print(devia)
        deviaSel = devia.drop([10,100,1000,10000], axis=1)
        devMax = np.amax(np.absolute(deviaSel.values))
        print('maximum deviation:')
        print(devMax)

def fileIterSize(mainFolderName):
    df = inspect('%s/%s' % (mainFolderName, folder) )
    df.to_csv('%s/%s.csv' % (mainFolderName, folder), index=False)
    df = pd.read_csv('%s/%s.csv' % (mainFolderName, folder) )
    matrixIterSize(df, 'sizeIter')

def readBaseline(mainFolderName):
    method = 'separateMin'
    combinations = tools.getFolders(mainFolderName)
    if method == 'useGlobalMin':
        mins = pd.DataFrame(columns=['folder','appSize','routing','minTime'])
    elif method == 'separateMin':
        mins = pd.DataFrame(columns=['folder','appSize','routing','alpha','minTime','minAlloc'])
    for folder in combinations:
        appSize = folder.split('_')[3]
        routing = folder.split('_')[4]
        df = inspect('%s/%s' % (mainFolderName, folder) , folder)
        #df.to_csv('%s/%s.csv' % (mainFolderName, folder), index=False)
        if method == 'useGlobalMin':
            dfTimes = df['time(us)']
            minTime = min(dfTimes)
            print(minTime)
            mins.loc[len(mins)] = [folder, appSize, routing, minTime]
        elif method == 'separateMin':
            # for the items with identical alpha, get the min.
            for ialpha in list(set(df['alpha'])):
                oneAlpha = df[df['alpha']==ialpha]
                minTime = min(oneAlpha['time(us)'])
                minIdx = oneAlpha['time(us)'].idxmin(axis=0)
                minAlloc = oneAlpha.loc[minIdx]['alloc']
                mins.loc[len(mins)] = [folder, appSize, routing, ialpha, minTime, minAlloc]
    mins.to_csv('%s/minTimes.csv' % mainFolderName, index=False)
    print('file reading finished.')

def getMedian(df):
    dfMedian = pd.DataFrame(columns=df.columns)
    for alpha in list(set(df['alpha'])):
        for alloc in list(set(df['alloc'])):
            onePara = df[ (df['alpha']==alpha) & (df['alloc']==alloc) ]
            sample = onePara.iloc[0,:].copy()
            median = np.median( onePara['time(us)'] )
            sample['time(us)'] = median
            dfMedian.loc[len(dfMedian)] = sample
    return dfMedian

def readHybrid(mainFolderName):
    combinations = tools.getFolders(mainFolderName)
    allDF = []
    for folder in combinations:
        df = inspect('%s/%s' % (mainFolderName, folder), folder)
        #df.to_csv('%s/%s.csv' % (mainFolderName, folder), index=False)
        dfMedian = getMedian(df)
        #dfMedian.to_csv('%s/%s_median.csv' % (mainFolderName, folder), index=False)
        allDF.append(dfMedian)
    combinedDF = pd.concat(allDF, ignore_index=True)
    combinedDF.to_csv('%s/Hybrid_combined.csv' % (mainFolderName), index=False)

def bestBase(mainFolderName):
    df = pd.read_csv('%s/minTimes.csv' % (mainFolderName) )
    dfpiv = pd.pivot_table(df, index=['appSize'], columns=['routing','alpha'], values='minTime')
    dfpiv.sort_index(axis=0, level='appSize', ascending=True, inplace=True)
    dfpiv.to_csv('%s/minTimes_pivot.csv' % (mainFolderName) )

def bestAlloc(mainFolderName):
    df = pd.read_csv('%s/Hybrid_combined.csv' % (mainFolderName) )
    dfpiv = pd.pivot_table(df, index=['smallNum','smallSize','largeNum','largeSize'], columns=['routing','alpha','alloc'], values='time(us)')
    dfpiv.sort_index(axis=0, level='largeNum', ascending=True, inplace=True)
    dfpiv = dfpiv.reindex_axis(['hybrid','simple','spread','random'], axis=1, level='alloc')
    print(dfpiv.columns)
    dfpiv.to_csv('%s/Hybrid_combined_pivot.csv' % (mainFolderName) )
    # first get the best allocation line by line.
    bestIdx = []
    for i in range( int( len(df)/4 ) ):
        oneCase = df.iloc[ range(4*i, 4*(i+1) ) ][['time(us)']]
        minIdx = oneCase.idxmin(axis=0)['time(us)']
        bestIdx.append(minIdx)
    dfBestAlloc = df.iloc[bestIdx]
    #print(dfBestAlloc)
    piv = pd.pivot_table(dfBestAlloc, index=['smallNum','smallSize','largeNum','largeSize'], columns=['routing','alpha'], values='alloc',
            aggfunc=lambda x: ' '.join(x) )
    piv.sort_index(axis=0, level='largeNum', ascending=True, inplace=True)
    piv.to_csv('%s/Hybrid_bestAlloc.csv' % (mainFolderName) )

if __name__ == '__main__':
    main()
