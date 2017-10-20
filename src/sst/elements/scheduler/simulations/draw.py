#!/usr/bin/env python
"""
@author: Yijia Zhang

Draw hybrid allocation project graphs.
Including graphs for the SC paper.

run by:


### TODO ###


### warning ###
for loop for cases changed.

"""
import sys
#=========================

#=========================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def setStyle(snsns):
    snsns.set_style('whitegrid',{'grid.color':'.15','axes.edgecolor':'.15'})
#    print(snsns.axes_style())

def draw(df, mode, groupNum, routersPerGroup, nodesPerRouter, utilization, application, messageSize, messageIter, traceMode, scheduler, routing, alpha):
    import seaborn as sns
    
    if mode == 'mixIterRaw':
        dfThis = df
    else:
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
                    ].copy()
                
#    if mode == 'normalSum' or mode == 'SumComp':
        # get the summary improvement.
#        r_simple = []
#        r_random = []
#        r_dflyrdr = []
#        r_dflyrdg = []
#        r_dflyrrn = []
#        r_dflyrrr = []
#        r_dflyslurm = []
#        r_dflyhybridbf = []
#        r_dflyhybridthres2 = []
        
#        overall = (1/avg_dflyslurm + 1/avg_simple + 1/avg_dflyrdr + 1/avg_dflyrdg + 1/avg_dflyrrr + 1/avg_random + 1/avg_dflyrrn) / 7
        
#        print('Overall improvement: %d%%' % int( (1 - overall)*100) )
#        print('Improvement up to: %d%%' % int( (1 - 1/avg_dflyrrn)*100) )
#        print('Slurm is slower by %d%%.' % ( int( (avg_dflyslurm - 1) * 100 ) ) )
#        print('Simple is slower by %d%%.' % ( int( (avg_simple - 1) * 100 ) ) )
#        print('RDR is slower by %d%%.' % ( int( (avg_dflyrdr - 1) * 100 ) ) )
#        print('RDG is slower by %d%%.' % ( int( (avg_dflyrdg - 1) * 100 ) ) )
#        print('RRR is slower by %d%%.' % ( int( (avg_dflyrrr - 1) * 100 ) ) )
#        print('RDN is slower by %d%%.' % ( int( (avg_random - 1) * 100 ) ) )
#        print('RRN is slower by %d%%.' % ( int( (avg_dflyrrn - 1) * 100 ) ) )
#        print('HybridBF is slower by %d%%.' % ( int( (avg_dflyhybridbf - 1) * 100 ) ) )
#        print('HybridThres2 is slower by %d%%.' % ( int( (avg_dflyhybridthres2 - 1) * 100 ) ) )
                
    # change the names for drawing.
#    else:
    dfThis.replace('dflyhybrid','Hybrid',inplace=True)
    dfThis.replace('dflyhybridbf','Hybrid\n-BestFit',inplace=True)
    dfThis.replace('dflyhybridthres2','Hybrid\n-IncThres',inplace=True)
    dfThis.replace('dflyhybridrn','Hybrid\n-Random',inplace=True)
    dfThis.replace('dflyslurm','Slurm',inplace=True)
    dfThis.replace('simple','Simple',inplace=True)
    dfThis.replace('random','RDN',inplace=True)
    dfThis.replace('dflyrdr','RDR',inplace=True)
    dfThis.replace('dflyrdg','RDG',inplace=True)
    dfThis.replace('dflyrrn','RRN',inplace=True)
    dfThis.replace('dflyrrr','RRR',inplace=True)
    xname = 'Corner Case Index' if traceMode == 'corner' else 'Random Case Index'
    if traceMode == 'corner':
        dfThis.loc[:, 'traceNum'].replace(5,0,inplace=True)
        dfThis.loc[:, 'traceNum'].replace(6,5,inplace=True)
        dfThis.loc[:, 'traceNum'].replace(7,6,inplace=True)
        dfThis.loc[:, 'traceNum'].replace(4,0,inplace=True)
        dfThis.loc[:, 'traceNum'].replace(18,4,inplace=True)
    dfThis.rename(columns={'traceNum':xname}, inplace=True)
    if mode == 'mixIterRaw':
        pass
    else:
        dfThis.rename(columns={'Avg.Norm.Latency':'Avg. Performance Slowdown'}, inplace=True)

    # drawing.
    if mode == 'normal':
        dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
        sns.set(font_scale=7)
        setStyle(sns)
        g = sns.factorplot(data=dfThis, kind='bar', ci=None, size=20, aspect=3.5, x=xname, y='Avg. Performance Slowdown',
                       hue='Allocation\nPolicy', hue_order=['Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN']
#                       hue='allocation', hue_order=['Hybrid','Hybrid_Random','Hybrid_BestFit','Hybrid_IncThres']
                       , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                       )
    elif mode == 'normalSum':
        sumdf = pd.DataFrame(columns=['Allocation Policy','Avg. of Normalized APS'])
        cases = range(1, 50+1)
        for icase in cases:
            case = dfThis[ dfThis[xname]==icase ]
            hybrid = case[ case['allocation']=='Hybrid' ]['Avg. Performance Slowdown'].mean()
            sumdf.loc[len(sumdf)] = [ 'Hybrid', 1]
            sumdf.loc[len(sumdf)] = [ 'Slurm', case[ case['allocation']=='Slurm' ]['Avg. Performance Slowdown'].mean() / hybrid ]
            sumdf.loc[len(sumdf)] = [ 'Simple', case[ case['allocation']=='Simple' ]['Avg. Performance Slowdown'].mean() / hybrid ]
            sumdf.loc[len(sumdf)] = [ 'RDN', case[ case['allocation']=='RDN' ]['Avg. Performance Slowdown'].mean() / hybrid ]
            sumdf.loc[len(sumdf)] = [ 'RDR', case[ case['allocation']=='RDR' ]['Avg. Performance Slowdown'].mean() / hybrid ]
            sumdf.loc[len(sumdf)] = [ 'RDG', case[ case['allocation']=='RDG' ]['Avg. Performance Slowdown'].mean() / hybrid ]
            sumdf.loc[len(sumdf)] = [ 'RRN', case[ case['allocation']=='RRN' ]['Avg. Performance Slowdown'].mean() / hybrid ]
            sumdf.loc[len(sumdf)] = [ 'RRR', case[ case['allocation']=='RRR' ]['Avg. Performance Slowdown'].mean() / hybrid ]
        rdr = sumdf[ (sumdf['Allocation Policy']=='RDR') ]['Avg. of Normalized APS'].mean()
        print('hybrid better than rdr for %s%%' % ((1-1/rdr)*100) )
        sns.set(font_scale=3.5)
        setStyle(sns)
#        sumdf = pd.DataFrame([
#                              ['Hybrid', 1],
#                              ['Slurm', avg_dflyslurm],
#                              ['Simple', avg_simple],
#                              ['RDR', avg_dflyrdr],
#                              ['RDG', avg_dflyrdg],
#                              ['RRR', avg_dflyrrr],
#                              ['RDN', avg_random],
#                              ['RRN', avg_dflyrrn],
#                                ], columns=['allocation','Avg. of Normalized APS'])
        g = sns.factorplot(data=sumdf, kind='bar', ci=99.73, size=10, aspect=2, x='Allocation Policy', y='Avg. of Normalized APS', capsize=0.4
                           , order=['Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN']
                           , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                           )
    elif mode == 'SumComp':
        sumdf = pd.DataFrame(columns=['Variants of hybrid allocation policy','Avg. of Normalized APS'])
        cases = range(1, 50+1)
        for icase in cases:
            case = dfThis[ dfThis[xname]==icase ]
            hybrid = case[ case['allocation']=='Hybrid' ]['Avg. Performance Slowdown'].mean()
            sumdf.loc[len(sumdf)] = [ 'Hybrid', 1]
            sumdf.loc[len(sumdf)] = [ 'Hybrid\n-Random', case[ case['allocation']=='Hybrid\n-Random' ]['Avg. Performance Slowdown'].mean() / hybrid ]
            sumdf.loc[len(sumdf)] = [ 'Hybrid\n-BestFit', case[ case['allocation']=='Hybrid\n-BestFit' ]['Avg. Performance Slowdown'].mean() / hybrid ]
            sumdf.loc[len(sumdf)] = [ 'Hybrid\n-IncThres', case[ case['allocation']=='Hybrid\n-IncThres' ]['Avg. Performance Slowdown'].mean() / hybrid ]
        sns.set(font_scale=4)
        setStyle(sns)
#        sumdf = pd.DataFrame([
#                              ['Hybrid', 1],
#                              ['Slurm', avg_dflyslurm],
#                              ['Simple', avg_simple],
#                              ['RDR', avg_dflyrdr],
#                              ['RDG', avg_dflyrdg],
#                              ['RRR', avg_dflyrrr],
#                              ['RDN', avg_random],
#                              ['RRN', avg_dflyrrn],
#                                ], columns=['allocation','Avg. of Normalized APS'])
        g = sns.factorplot(data=sumdf, kind='bar', ci=99.73, size=10, aspect=2, x='Variants of hybrid allocation policy', y='Avg. of Normalized APS', capsize=0.4
                           , order=['Hybrid','Hybrid\n-BestFit','Hybrid\n-Random','Hybrid\n-IncThres']
                           , palette=sns.light_palette('green', n_colors=5, reverse=True)
                           )
        sns.plt.ylim(0.9, 1.3)
    elif mode == 'motivation':
        dfThis.loc[dfThis[xname]==2,'Avg. Performance Slowdown'] = dfThis[dfThis[xname]==2]['Avg. Performance Slowdown'] * 7.615
        dfThis.loc[dfThis[xname]==4,'Avg. Performance Slowdown'] = dfThis[dfThis[xname]==4]['Avg. Performance Slowdown'] * 165.303
        dfThis.loc[:,'Corner Case Index'].replace(2, 'Workload 1:\nseventeen 16-node jobs', inplace=True)
        dfThis.loc[:,'Corner Case Index'].replace(4, 'Workload 2:\ntwo 136-node jobs', inplace=True)
        dfThis.rename(columns={'Corner Case Index':'Parallel Workloads'}, inplace=True)
        dfThis.rename(columns={'Avg. Performance Slowdown':'Avg. Communication Time (ms)'}, inplace=True)
        dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
        sns.set(font_scale=4)
        setStyle(sns)
        g = sns.factorplot(data=dfThis, kind='bar', ci=None, size=15, aspect=1, x='Parallel Workloads', y='Avg. Communication Time (ms)',
                       hue='Allocation\nPolicy', hue_order=['RDG','RDN']
                       , order=['Workload 1:\nseventeen 16-node jobs','Workload 2:\ntwo 136-node jobs']
                       )
    elif mode == 'order1':
        dfThis.loc[:,'Corner Case Index'].replace(6, 'Prioritize larger jobs', inplace=True)# 6 is originally 7.
        dfThis.loc[:,'Corner Case Index'].replace(8, 'Prioritize smaller jobs', inplace=True)
        dfThis.rename(columns={'Corner Case Index':'Workload A'}, inplace=True)
        dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
        sns.set(font_scale=7)
        setStyle(sns)
        g = sns.factorplot(data=dfThis, kind='bar', ci=None, size=20, aspect=2, x='Workload A', y='Avg. Performance Slowdown',
                       hue='Allocation\nPolicy', hue_order=['Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN'],
                       order=['Prioritize larger jobs','Prioritize smaller jobs']
                       , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                       )
    elif mode == 'order2':
        dfThis.loc[:,'Corner Case Index'].replace(9, 'Prioritize larger jobs', inplace=True)
        dfThis.loc[:,'Corner Case Index'].replace(10, 'Prioritize smaller jobs', inplace=True)
        dfThis.rename(columns={'Corner Case Index':'Workload A'}, inplace=True)
        dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
        smallFirst = dfThis[ (dfThis['Workload A']=='Prioritize smaller jobs') & (dfThis['Allocation\nPolicy']=='Hybrid') ]['Avg. Performance Slowdown'].values[0]
        largeFirst = dfThis[ (dfThis['Workload A']=='Prioritize larger jobs') & (dfThis['Allocation\nPolicy']=='Hybrid') ]['Avg. Performance Slowdown'].values[0]
        print(1-smallFirst/largeFirst)
        sns.set(font_scale=7)
        setStyle(sns)
        g = sns.factorplot(data=dfThis, kind='bar', ci=None, size=20, aspect=2, x='Workload A', y='Avg. Performance Slowdown',
                       hue='Allocation\nPolicy', hue_order=['Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN'],
                       order=['Prioritize larger jobs','Prioritize smaller jobs']
                       , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                       )
    elif mode == 'normalCorner':
#        dfThis.loc[len(dfThis),:] = [groupNum, routersPerGroup, nodesPerRouter, utilization, application, messageSize, messageIter, traceMode, 'average'...]
        dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
        sns.set(font_scale=7)
        setStyle(sns)
        g = sns.factorplot(data=dfThis, kind='bar', ci=None, size=20, aspect=2, x=xname, y='Avg. Performance Slowdown',
                       hue='Allocation\nPolicy', hue_order=['Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN'],
                       order=[1,2,3,4,5,6]
                       , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                       )
    elif mode in ['optimum', 'optimum21']:
        hybrid = dfThis[dfThis['allocation']=='Hybrid']['Avg. Performance Slowdown'].mean()
        print('hybrid APS: %.4f' % hybrid)
        randomMin = dfThis[dfThis['allocation']=='RDN']['Avg. Performance Slowdown'].min()
        print('random min APS: %.4f' % (randomMin) )
        dfGood = dfThis[ (dfThis['allocation']=='RDN') & (dfThis['Avg. Performance Slowdown']<1.43) ]# change the value here.
        print('number of random better than hybrid: %d' % len(dfGood) )
        print(dfGood[['expIter', 'Avg. Performance Slowdown']])
        random20 = dfThis[dfThis['allocation']=='RDN'].iloc[range(20)]['Avg. Performance Slowdown'].mean()
        random20CI = dfThis[dfThis['allocation']=='RDN'].iloc[range(20)]['Avg. Performance Slowdown'].std() * 2
        randomAll = dfThis[dfThis['allocation']=='RDN']['Avg. Performance Slowdown'].mean()
        print('random 20 average: %.4f+-%.4f (95%%), random all average: %.4f' % (random20, random20CI, randomAll))
        
        dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
        sns.set(font_scale=2)
        setStyle(sns)
#        g = sns.factorplot(data=dfThis, kind='box', size=20, aspect=2, x=xname, y='Avg. Performance Slowdown',
#                       hue='Allocation\nPolicy', hue_order=['Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN'],
#                       order=[21]
#                       , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
#                       )
        g = sns.distplot(dfThis[(dfThis['Allocation\nPolicy']=='RDN') & (dfThis['expIter']<100000)]['Avg. Performance Slowdown'])
#        g = sns.distplot(dfThis[dfThis['Allocation\nPolicy']=='Hybrid']['Avg. Performance Slowdown'])
        g = g.get_figure()
    elif mode == 'mixIter':
        sns.set(font_scale=6)
        setStyle(sns)
        dfThis.loc[:,'Corner Case Index'].replace(6, 'normal small jobs', inplace=True)
        dfThis.loc[:,'Corner Case Index'].replace(16, 'Iteration-increased small jobs', inplace=True)
        dfThis.rename(columns={'Corner Case Index':'Corner case 6: two large jobs and many small jobs'}, inplace=True)
        dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
        g = sns.factorplot(data=dfThis, kind='bar', ci=None, size=20, aspect=2, x='Corner case 6: two large jobs and many small jobs',
                       y='Avg. Performance Slowdown',
                       hue='Allocation\nPolicy', hue_order=['Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN'],
                       order=['normal small jobs','Iteration-increased small jobs']
                       , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                       )
    elif mode == 'mixMessageSize':
        sns.set(font_scale=6)
        setStyle(sns)
        dfThis.loc[:,'Corner Case Index'].replace(6, 'normal small jobs', inplace=True)
        dfThis.loc[:,'Corner Case Index'].replace(19, 'MessageSize-increased small jobs', inplace=True)
        dfThis.rename(columns={'Corner Case Index':'Corner case 6: two large jobs and many small jobs'}, inplace=True)
        dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
        g = sns.factorplot(data=dfThis, kind='bar', ci=99.7, size=20, aspect=2, x='Corner case 6: two large jobs and many small jobs',
                       y='Avg. Performance Slowdown',
                       hue='Allocation\nPolicy', hue_order=['Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN'],
                       order=['normal small jobs','MessageSize-increased small jobs']
                       , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                       )
    elif mode == 'mixIterRaw':
        sns.set(font_scale=6)
        setStyle(sns)
        # input the value manually here.
        dfThis.loc[len(dfThis)] = [17,4,4,100,'alltoall',1000,1,'corner',6,'Baseline','topo','easy','adaptive',1,0,4,1328]
        dfThis.loc[len(dfThis)] = [17,4,4,100,'alltoall',1000,100,'corner',16,'Baseline','topo','easy','adaptive',1,0,4,132800]
        dfThis.loc[len(dfThis)] = [17,4,4,100,'alltoall',1000,1,'corner',6,'Baseline','topo','easy','adaptive',1,0,32,20751]
        dfThis.loc[len(dfThis)] = [17,4,4,100,'alltoall',1000,1,'corner',16,'Baseline','topo','easy','adaptive',1,0,32,20751]

        dfSize = dfThis[dfThis['jobSize']==16].copy()
        dfSize.loc[:,'Corner Case Index'].replace(24, 'normal small jobs', inplace=True)
        dfSize.loc[:,'Corner Case Index'].replace(25, 'Iteration-increased small jobs', inplace=True)
        dfSize.rename(columns={'Corner Case Index':'Corner case 6: two large jobs and many small jobs'}, inplace=True)
        dfSize.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
        g = sns.factorplot(data=dfSize, kind='bar', ci=99.7, size=20, aspect=2, x='Corner case 6: two large jobs and many small jobs',
                       y='time(us)', capsize=0.04,
                       hue='Allocation\nPolicy', hue_order=['Baseline','Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN'],
                       order=['normal small jobs']#'normal small jobs','Iteration-increased small jobs'
                       , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                       )
#        sns.plt.ylim(0, 1000000)
    elif mode == 'compHybrid':
        hybrid3 = dfThis[ (dfThis['allocation']=='Hybrid') & (dfThis[xname]==3) ]['Avg. Performance Slowdown'].mean()
        hybridrn3 = dfThis[ (dfThis['allocation']=='Hybrid\n-Random') & (dfThis[xname]==3) ]['Avg. Performance Slowdown'].mean()
        print('hybridrn better in case 3 for %s%%' % (100*(1-hybridrn3/hybrid3)) )
        hybrid6 = dfThis[ (dfThis['allocation']=='Hybrid') & (dfThis[xname]==6) ]['Avg. Performance Slowdown'].mean()
        hybridrn6 = dfThis[ (dfThis['allocation']=='Hybrid\n-Random') & (dfThis[xname]==6) ]['Avg. Performance Slowdown'].mean()
        print('hybridrn better in case 6 for %s%%' % (100*(hybridrn6/hybrid6-1)) )

        sns.set(font_scale=8)
        setStyle(sns)
        thisColor = 'green'
        dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
        if traceMode == 'corner':
            g = sns.factorplot(data=dfThis, kind='bar', ci=None, size=20, aspect=2, x=xname, y='Avg. Performance Slowdown',
                           hue='Allocation\nPolicy', hue_order=['Hybrid','Hybrid\n-BestFit','Hybrid\n-Random','Hybrid\n-IncThres']
                           , order=[1,2,3,4,5,6]
                           , palette=sns.light_palette(thisColor, n_colors=5, reverse=True)
                           )
        else:
            g = sns.factorplot(data=dfThis, kind='bar', ci=None, size=20, aspect=4, x=xname, y='Avg. Performance Slowdown',
                           hue='Allocation\nPolicy', hue_order=['Hybrid','Hybrid_BestFit','Hybrid_Random','Hybrid_IncThres']
                           , palette=sns.light_palette(thisColor, n_colors=5, reverse=True)
                           )
#        sns.plt.ylim(0.6, 1.4)


#    g.fig.suptitle('g=%d, a=%d, p=%d, utilization=%d%%, \napp=%s, alpha=%.2f\n' % (groupNum, routersPerGroup, nodesPerRouter, utilization, application, 
#                                                            alpha))
#    sns.plt.ylim(0, 7)
#    sns.plt.xlim(8, 12)
#    sns.plt.show()
    g.savefig('hybrid/%d_%d_%d_%d_%s_%d_%d_%s_%s_%s_%.2f_%s.png' % (groupNum, routersPerGroup, nodesPerRouter, utilization, application, 
                                                            messageSize, messageIter, traceMode, scheduler, routing, alpha, mode) )

def simpleDraw(df, mode, groupNum, routersPerGroup, nodesPerRouter, utilization, application, messageSize, messageIter, traceMode, scheduler, routing, alpha):
    import seaborn as sns
    smallFirst = df[ (df['traceNum']==1) & (df['allocation']=='dflyhybrid') ]['Avg.Norm.Latency'].values[0]
    largeFirst = df[ (df['traceNum']==2) & (df['allocation']=='dflyhybrid') ]['Avg.Norm.Latency'].values[0]
#    smallFirst = df[ (df['traceNum']==1) & (df['allocation']=='dflyrrr') ]['Avg.Norm.Latency'].values[0]
#    largeFirst = df[ (df['traceNum']==2) & (df['allocation']=='dflyrrr') ]['Avg.Norm.Latency'].values[0]
    print(smallFirst)
    print(largeFirst)
    df.loc[len(df)] = [17,4,4,100,'alltoall',10**5,1,'order',0,'Hybrid\n-small\n-first','topo','easy','adaptive',1,0,smallFirst]
    df.loc[len(df)] = [17,4,4,100,'alltoall',10**5,1,'order',0,'Hybrid\n-large\n-first','topo','easy','adaptive',1,0,largeFirst]
#    df.append([17,4,4,100,'alltoall',10**5,1,'order',0,'Hybrid\n_small\n_first','topo','easy','adaptive',1,0,smallFirst])
#    df.append([17,4,4,100,'alltoall',10**5,1,'order',0,'Hybrid\n_large\n_first','topo','easy','adaptive',1,0,largeFirst])

    df.replace('dflyhybrid','Hybrid',inplace=True)
    df.replace('dflyhybridbf','Hybrid\n_BestFit',inplace=True)
    df.replace('dflyhybridthres2','Hybrid\n_IncThres',inplace=True)
    df.replace('dflyslurm','Slurm',inplace=True)
    df.replace('simple','Simple',inplace=True)
    df.replace('random','RDN',inplace=True)
    df.replace('dflyrdr','RDR',inplace=True)
    df.replace('dflyrdg','RDG',inplace=True)
    df.replace('dflyrrn','RRN',inplace=True)
    df.replace('dflyrrr','RRR',inplace=True)
    xname = 'Corner Case Index' if traceMode == 'corner' else 'Random Case Index'
    df.rename(columns={'traceNum':xname}, inplace=True)
    df.rename(columns={'Avg.Norm.Latency':'Avg. Performance Slowdown'}, inplace=True)
    df.rename(columns={'allocation':'Allocation Policy'}, inplace=True)
    
    mean = df[ df['Allocation Policy']=='Hybrid' ]['Avg. Performance Slowdown'].mean()
    print(mean)
    print( 'better for %s%%' %  ((1-smallFirst/mean)*100) )

    sns.set(font_scale=4.5)
    setStyle(sns)
    g = sns.factorplot(data=df, kind='box', ci=None, size=15, aspect=2, x='Allocation Policy', y='Avg. Performance Slowdown', showfliers=False,
                       order=['Hybrid\n-small\n-first','Hybrid\n-large\n-first','Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN']
                       , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                       )
#    sns.plt.ylim(1.5, 3.5)
#    g.fig.suptitle('g=%d, a=%d, p=%d, utilization=%d%%, \napp=%s, alpha=%.2f\n' % (groupNum, routersPerGroup, nodesPerRouter, utilization, application, 
#                                                            alpha))
    g.savefig('hybrid/%d_%d_%d_%d_%s_%d_%d_%s_%s_%s_%.2f_%s.png' % (groupNum, routersPerGroup, nodesPerRouter, utilization, application, 
                                                            messageSize, messageIter, traceMode, scheduler, routing, alpha, mode) )


def statDraw(df, traceMode, portType, statName):
    import seaborn as sns
    dfThis = df[df['portType']==portType].copy()

    xname = 'Corner Case Index' if traceMode == 'corner' else 'Random Case Index'
    dfThis.replace('dflyhybrid','Hybrid',inplace=True)
    dfThis.replace('dflyslurm','Slurm',inplace=True)
    dfThis.replace('simple','Simple',inplace=True)
    dfThis.replace('random','RDN',inplace=True)
    dfThis.replace('dflyrdr','RDR',inplace=True)
    dfThis.replace('dflyrdg','RDG',inplace=True)
    dfThis.replace('dflyrrn','RRN',inplace=True)
    dfThis.replace('dflyrrr','RRR',inplace=True)
    xname = 'Corner Case Index' if traceMode == 'corner' else 'Random Case Index'
    if traceMode == 'corner':
        dfThis.loc[:, 'traceNum'].replace(5,0,inplace=True)
        dfThis.loc[:, 'traceNum'].replace(6,5,inplace=True)
        dfThis.loc[:, 'traceNum'].replace(7,6,inplace=True)
        dfThis.loc[:, 'traceNum'].replace(4,0,inplace=True)
        dfThis.loc[:, 'traceNum'].replace(18,4,inplace=True)
    dfThis.rename(columns={'traceNum':xname}, inplace=True)
#    print(dfThis.columns)
    if statName == 'send_packet_count' and portType == 'global':
        changedName = 'Packet Count on Global Links'
        dfThis.rename(columns={'send_packet_count':changedName}, inplace=True)
    elif statName == 'send_packet_count' and portType == 'local':
        changedName = 'Packet Count on Local Links'
        dfThis.rename(columns={'send_packet_count':changedName}, inplace=True)
    elif statName == 'output_port_stalls' and portType == 'global':
        changedName = 'Stall Count of Output Ports\ntowards Global Links'
        dfThis.rename(columns={'output_port_stalls':changedName}, inplace=True)
    elif statName == 'output_port_stalls' and portType == 'local':
        changedName = 'Stall Count of Output Ports\ntowards Local Links'
        dfThis.rename(columns={'output_port_stalls':changedName}, inplace=True)

    dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
    sns.set(font_scale=7)
    setStyle(sns)
    g = sns.factorplot(data=dfThis, kind='bar', ci=99.73, size=20, aspect=2, x=xname, y=changedName, capsize=0.06, #showfliers=False,
                       hue='Allocation\nPolicy', hue_order=['Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN']
                       , order=[22,27,26]#[1,2,3,4,5,6]
                       , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                       )
#    g.fig.suptitle('Network statistics, portType=%s' % (portType) )
#    sns.plt.ylim(0, 20000)
#    sns.plt.show()
#    g.savefig('hybrid/networkStat_alltoall_%s_%s_%s.png' % (traceMode, portType, statName) )
    g.savefig('hybrid/networkStat_bcast_%s_%s_%s.png' % (traceMode, portType, statName) )
    
def separate(small, large, groupNum, routersPerGroup, nodesPerRouter, utilization, application, messageSize, messageIter, traceMode, scheduler, routing, alpha):
    import seaborn as sns
    
    xname = 'Job Type'
    smallThis = small[
                (small['groupNum']==groupNum)
                & (small['routersPerGroup']==routersPerGroup)
                & (small['nodesPerRouter']==nodesPerRouter)
                & (small['utilization']==utilization)
                & (small['application']==application)
                & (small['messageSize']==messageSize)
                & (small['messageIter']==messageIter)
                & (small['traceMode']==traceMode)
                & (small['scheduler']==scheduler)
                & (small['routing']==routing)
                & (small['alpha']==alpha)
                ].copy()
    smallThis[xname] = ['4-node jobs']*len(smallThis)
    largeThis = large[
                (large['groupNum']==groupNum)
                & (large['routersPerGroup']==routersPerGroup)
                & (large['nodesPerRouter']==nodesPerRouter)
                & (large['utilization']==utilization)
                & (large['application']==application)
                & (large['messageSize']==messageSize)
                & (large['messageIter']==messageIter)
                & (large['traceMode']==traceMode)
                & (large['scheduler']==scheduler)
                & (large['routing']==routing)
                & (large['alpha']==alpha)
                ].copy()
    largeThis[xname] = ['32-node jobs']*len(largeThis)
    dfThis = pd.concat([smallThis, largeThis], ignore_index=True)

    # change the names for drawing.
    dfThis.replace('dflyhybrid','Hybrid',inplace=True)
    dfThis.replace('dflyhybridbf','Hybrid_BestFit',inplace=True)
    dfThis.replace('dflyhybridthres2','Hybrid_IncThres',inplace=True)
    dfThis.replace('dflyslurm','Slurm',inplace=True)
    dfThis.replace('simple','Simple',inplace=True)
    dfThis.replace('random','RDN',inplace=True)
    dfThis.replace('dflyrdr','RDR',inplace=True)
    dfThis.replace('dflyrdg','RDG',inplace=True)
    dfThis.replace('dflyrrn','RRN',inplace=True)
    dfThis.replace('dflyrrr','RRR',inplace=True)
    dfThis.rename(columns={'Avg.Norm.Latency':'Separate APS'}, inplace=True)
    dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)

    sns.set(font_scale=7)
    setStyle(sns)
    g = sns.factorplot(data=dfThis, kind='bar', ci=None, size=20, aspect=2, x=xname, y='Separate APS',
                   hue='Allocation\nPolicy', hue_order=['Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN']
                   , palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                   )
#    g.fig.suptitle('g=%d, a=%d, p=%d, utilization=%d%%, \napp=%s, alpha=%.2f\n' % (groupNum, routersPerGroup, nodesPerRouter, utilization, application, 
#                                                            alpha))
#    sns.plt.ylim(0, 7)
#    sns.plt.xlim(8, 12)
#    sns.plt.show()
    g.savefig('hybrid/%d_%d_%d_%d_%s_%d_%d_%s_%s_%s_%.2f_%s.png' % (groupNum, routersPerGroup, nodesPerRouter, utilization, application, 
                                                            messageSize, messageIter, traceMode, scheduler, routing, alpha, 'separate') )

def comparaParaGenDF(df, para, mode, name, groupNum, routersPerGroup, nodesPerRouter, utilization, application, messageSize, messageIter, traceMode, scheduler, routing, alpha):
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
                ].copy()
                
    if mode == 'normalSum' or mode == 'SumComp':
        # get the summary improvement.
        r_simple = []
        r_random = []
        r_dflyrdr = []
        r_dflyrdg = []
        r_dflyrrn = []
        r_dflyrrr = []
        r_dflyslurm = []
        r_dflyhybridbf = []
        r_dflyhybridthres2 = []
        cases = range(1, 50+1) if traceMode == 'random' else [1,2,3,4,5,6,7]
        for icase in cases:
            case = dfThis[ dfThis['traceNum']==icase ]
            hybrid = case[ case['allocation']=='dflyhybrid' ]['Avg.Norm.Latency'].mean()
            r_simple.append( case[ case['allocation']=='simple' ]['Avg.Norm.Latency'].mean() / hybrid )
            r_random.append( case[ case['allocation']=='random' ]['Avg.Norm.Latency'].mean() / hybrid )
            r_dflyslurm.append( case[ case['allocation']=='dflyslurm' ]['Avg.Norm.Latency'].mean() / hybrid )
            r_dflyhybridbf.append( case[ case['allocation']=='dflyhybridbf' ]['Avg.Norm.Latency'].mean() / hybrid )
            r_dflyhybridthres2.append( case[ case['allocation']=='dflyhybridthres2' ]['Avg.Norm.Latency'].mean() / hybrid )
            r_dflyrdr.append( case[ case['allocation']=='dflyrdr' ]['Avg.Norm.Latency'].mean() / hybrid )
            r_dflyrdg.append( case[ case['allocation']=='dflyrdg' ]['Avg.Norm.Latency'].mean() / hybrid )
            r_dflyrrn.append( case[ case['allocation']=='dflyrrn' ]['Avg.Norm.Latency'].mean() / hybrid )
            r_dflyrrr.append( case[ case['allocation']=='dflyrrr' ]['Avg.Norm.Latency'].mean() / hybrid )
#            print(hybrid)
        avg_dflyslurm = sum(r_dflyslurm)/len(r_dflyslurm)
        avg_simple = sum(r_simple)/len(r_simple)
        avg_dflyrdr = sum(r_dflyrdr)/len(r_dflyrdr)
        avg_dflyrdg = sum(r_dflyrdg)/len(r_dflyrdg)
        avg_dflyrrr = sum(r_dflyrrr)/len(r_dflyrrr)
        avg_random = sum(r_random)/len(r_random)
        avg_dflyrrn = sum(r_dflyrrn)/len(r_dflyrrn)
#        avg_dflyhybridbf = sum(r_dflyhybridbf)/len(r_dflyhybridbf)
#        avg_dflyhybridthres2 = sum(r_dflyhybridthres2)/len(r_dflyhybridthres2)
        
        overall = (1/avg_dflyslurm + 1/avg_simple + 1/avg_dflyrdr + 1/avg_dflyrdg + 1/avg_dflyrrr + 1/avg_random + 1/avg_dflyrrn) / 7
        
        print('Overall improvement: %d%%' % int( (1 - overall)*100) )
        print('Slurm is slower by %d%%.' % ( int( (avg_dflyslurm - 1) * 100 ) ) )
        print('Simple is slower by %d%%.' % ( int( (avg_simple - 1) * 100 ) ) )
        print('RDR is slower by %d%%.' % ( int( (avg_dflyrdr - 1) * 100 ) ) )
        print('RDG is slower by %d%%.' % ( int( (avg_dflyrdg - 1) * 100 ) ) )
        print('RRR is slower by %d%%.' % ( int( (avg_dflyrrr - 1) * 100 ) ) )
        print('RDN is slower by %d%%.' % ( int( (avg_random - 1) * 100 ) ) )
        print('RRN is slower by %d%%.' % ( int( (avg_dflyrrn - 1) * 100 ) ) )
#        print('HybridBF is slower by %d%%.' % ( int( (avg_dflyhybridbf - 1) * 100 ) ) )
#        print('HybridThres2 is slower by %d%%.' % ( int( (avg_dflyhybridthres2 - 1) * 100 ) ) )
                
    # change the names for drawing.
    dfThis.replace('dflyhybrid','Hybrid',inplace=True)
    dfThis.replace('dflyhybridbf','Hybrid_BestFit',inplace=True)
    dfThis.replace('dflyhybridthres2','Hybrid_IncThres',inplace=True)
    dfThis.replace('dflyslurm','Slurm',inplace=True)
    dfThis.replace('simple','Simple',inplace=True)
    dfThis.replace('random','RDN',inplace=True)
    dfThis.replace('dflyrdr','RDR',inplace=True)
    dfThis.replace('dflyrdg','RDG',inplace=True)
    dfThis.replace('dflyrrn','RRN',inplace=True)
    dfThis.replace('dflyrrr','RRR',inplace=True)
    xname = 'Corner Case Index' if traceMode == 'corner' else 'Random Case Index'
    dfThis.rename(columns={'traceNum':xname}, inplace=True)
    dfThis.rename(columns={'Avg.Norm.Latency':'Avg. Performance Slowdown'}, inplace=True)
    
    sumdf = pd.DataFrame([
                          ['Hybrid', 1],
                          ['Slurm', avg_dflyslurm],
                          ['Simple', avg_simple],
                          ['RDR', avg_dflyrdr],
                          ['RDG', avg_dflyrdg],
                          ['RRR', avg_dflyrrr],
                          ['RDN', avg_random],
                          ['RRN', avg_dflyrrn],
                            ], columns=['allocation','Avg. of Normalized APS'])
    if para == 'pattern':
        sumdf[name] = [application] * len(sumdf)
    elif para == 'machine':
        sumdf[name] = [groupNum] * len(sumdf)
    elif para == 'messageSize':
        sumdf[name] = [messageSize] * len(sumdf)
    elif para == 'utilization':
        sumdf[name] = [utilization] * len(sumdf)
    elif para == 'alpha':
        sumdf[name] = [alpha] * len(sumdf)
    return sumdf
    
def comparePara(df, para):
    import seaborn as sns
    dfs = []
    if para == 'pattern':
        xname = 'Communication patterns'
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='allpingpong', messageSize=1000, messageIter=1000, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='stencil', messageSize=0, messageIter=2, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
    elif para == 'machine':
        xname = 'Machine Configurations'
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=9, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=33, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
        for idf in dfs:
            idf.loc[:, xname].replace(9,'g=9, a=4, p=4',inplace=True)
            idf.loc[:, xname].replace(17,'g=17, a=4, p=4',inplace=True)
            idf.loc[:, xname].replace(33,'g=33, a=4, p=4',inplace=True)
    elif para == 'messageSize':
        xname = 'Message size'
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=1000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
        for idf in dfs:
            idf.loc[:, xname].replace(1000,'1 KB',inplace=True)
            idf.loc[:, xname].replace(100000,'100 KB',inplace=True)
    elif para == 'utilization':
        xname = 'Machine Utilization Level'
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=50, application='alltoall', messageSize=100000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=100, application='alltoall', messageSize=100000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
        for idf in dfs:
            idf.loc[:, xname].replace(50,'50%',inplace=True)
            idf.loc[:, xname].replace(75,'75%',inplace=True)
            idf.loc[:, xname].replace(100,'100%',inplace=True)
    elif para == 'alpha':
        xname = 'Ratio of global link bandwidth to local link bandwidth'
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=0.25) )
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=1) )
        dfs.append( comparaParaGenDF(df, para, 'normalSum', xname, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
                    traceMode='random', scheduler='easy', routing='adaptive', alpha=4) )

    sumdf = pd.concat(dfs, ignore_index=True)
    sumdf.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
    
    sns.set(font_scale=8)
    setStyle(sns)
    thisColor = 'royalblue'
    g = sns.factorplot(data=sumdf, kind='bar', ci=None, size=20, aspect=2, x=xname, y='Avg. of Normalized APS'
                       , hue='Allocation\nPolicy'
                       , palette=sns.light_palette(thisColor, n_colors=11, reverse=True)
                       )
#    g.fig.suptitle('g=%d, a=%d, p=%d, utilization=%d%%, \napp=%s, alpha=%.2f\n' % (groupNum, routersPerGroup, nodesPerRouter, utilization, application, 
#                                                            alpha))
#    sns.plt.ylim(0, 7)
#    sns.plt.xlim(8, 12)
#    sns.plt.show()
    g.savefig('hybrid/comparePara_%s.png' % para)

def motivation(df, mode, groupNum, routersPerGroup, nodesPerRouter, utilization, application, messageSize, messageIter, traceMode, scheduler, routing, alpha):
    import seaborn as sns
    
    dfThis = df[# iteration ignored.
                (df['groupNum']==groupNum)
                & (df['routersPerGroup']==routersPerGroup)
                & (df['nodesPerRouter']==nodesPerRouter)
                & (df['utilization']==utilization)
                & (df['application']==application)
                & (df['messageSize']==messageSize)
                & (df['traceMode']==traceMode)
                & (df['scheduler']==scheduler)
                & (df['routing']==routing)
                & (df['alpha']==alpha)
                ].copy()

    random = dfThis[ (dfThis['allocation']=='random') & (dfThis['traceNum']==4) ]['time(us)'].mean()
    dflyrdg = dfThis[ (dfThis['allocation']=='dflyrdg') & (dfThis['traceNum']==4) ]['time(us)'].mean()
    print('better for %d%%' % ( (1 - random/dflyrdg)*100 ) )

    # change the names for drawing.
    dfThis['time(us)'] = dfThis['time(us)']/1000
    dfThis.replace('random','RDN',inplace=True)
    dfThis.replace('dflyrdg','RDG',inplace=True)
    dfThis.rename(columns={'traceNum':'Parallel Workloads'}, inplace=True)
    dfThis.rename(columns={'time(us)':'Avg. Communication Time (ms)'}, inplace=True)
    dfThis.loc[:,'Parallel Workloads'].replace(2, 'Workload 1:\nseventeen 16-node jobs', inplace=True)
    dfThis.loc[:,'Parallel Workloads'].replace(4, 'Workload 2:\ntwo 136-node jobs', inplace=True)
    dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)
    rdg1 = dfThis[ (dfThis['Allocation\nPolicy']=='RDG') & (dfThis['Parallel Workloads']=='Workload 1:\nseventeen 16-node jobs') ]['Avg. Communication Time (ms)'].mean()
    rdg2 = dfThis[ (dfThis['Allocation\nPolicy']=='RDG') & (dfThis['Parallel Workloads']=='Workload 2:\ntwo 136-node jobs') ]['Avg. Communication Time (ms)'].mean()
    rdn1 = dfThis[ (dfThis['Allocation\nPolicy']=='RDN') & (dfThis['Parallel Workloads']=='Workload 1:\nseventeen 16-node jobs') ]['Avg. Communication Time (ms)'].mean()
    rdn2 = dfThis[ (dfThis['Allocation\nPolicy']=='RDN') & (dfThis['Parallel Workloads']=='Workload 2:\ntwo 136-node jobs') ]['Avg. Communication Time (ms)'].mean()
    dfNew = pd.DataFrame([['Workload 1:\nseventeen 16-node jobs', 'RDG', 1],
                          ['Workload 2:\ntwo 136-node jobs', 'RDG', 1],
                          ['Workload 1:\nseventeen 16-node jobs', 'RDN', rdn1/rdg1],
                          ['Workload 2:\ntwo 136-node jobs', 'RDN', rdn2/rdg2]]
                        ,columns=['Parallel Workloads','Allocation\nPolicy','Communication Time\nNormalized w.r.t. RDG'])
    
    
    sns.set(font_scale=7)
    setStyle(sns)
    g = sns.factorplot(data=dfNew, kind='bar', ci=None, size=20, aspect=2, x='Parallel Workloads', y='Communication Time\nNormalized w.r.t. RDG',
                   hue='Allocation\nPolicy', hue_order=['RDG','RDN']
                   , order=['Workload 1:\nseventeen 16-node jobs','Workload 2:\ntwo 136-node jobs']
                   )
#    g = sns.factorplot(data=dfThis, kind='bar', ci=None, size=20, aspect=2, x='Parallel Workloads', y='Avg. Communication Time (ms)',
#                   hue='Allocation\nPolicy', hue_order=['RDG','RDN']
#                   , order=['Workload 1:\nseventeen 16-node jobs','Workload 2:\ntwo 136-node jobs']
#                   )
    sns.plt.ylim(0.6, 2)
    g.savefig('hybrid/%d_%d_%d_%d_%s_%d_%d_%s_%s_%s_%.2f_%s.png' % (groupNum, routersPerGroup, nodesPerRouter, utilization, application, 
                                                            messageSize, messageIter, traceMode, scheduler, routing, alpha, mode) )

def twoSizeJobs(df, mode, groupNum, routersPerGroup, nodesPerRouter, utilization, application, messageSize, messageIter, traceMode, traceNum, scheduler, routing, alpha):
    import seaborn as sns
    
    dfThis = df[
                (df['groupNum']==groupNum)
                & (df['routersPerGroup']==routersPerGroup)
                & (df['nodesPerRouter']==nodesPerRouter)
                & (df['utilization']==utilization)
                & (df['application']==application)
                & (df['messageSize']==messageSize)
                & (df['messageIter']==messageIter)
                & (df['traceMode']==traceMode)
                & (df['traceNum']==traceNum)
                & (df['scheduler']==scheduler)
                & (df['routing']==routing)
                & (df['alpha']==alpha)
                ].copy()

    # change the names for drawing.
    dfThis.replace('dflyhybrid','Hybrid',inplace=True)
    dfThis.replace('dflyhybridbf','Hybrid\n-BestFit',inplace=True)
    dfThis.replace('dflyhybridthres2','Hybrid\n-IncThres',inplace=True)
    dfThis.replace('dflyhybridrn','Hybrid\n-Random',inplace=True)
    dfThis.replace('dflyslurm','Slurm',inplace=True)
    dfThis.replace('simple','Simple',inplace=True)
    dfThis.replace('random','RDN',inplace=True)
    dfThis.replace('dflyrdr','RDR',inplace=True)
    dfThis.replace('dflyrdg','RDG',inplace=True)
    dfThis.replace('dflyrrn','RRN',inplace=True)
    dfThis.replace('dflyrrr','RRR',inplace=True)
    dfThis.rename(columns={'jobSize':'Job sizes'}, inplace=True)
    dfThis.rename(columns={'time(us)':'Avg. communication time (us)'}, inplace=True)
    dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)

    # drawing.
    if mode == 'asdf':
        sns.set(font_scale=6)
        setStyle(sns)

        g = sns.factorplot(data=dfThis, kind='bar', ci=99.7, size=20, aspect=2, x='Job sizes',
                       y='Avg. communication time (us)', capsize=0.04,
                       hue='Allocation\nPolicy', hue_order=['Hybrid','Slurm','Simple','RDR','RDG','RRR','RDN','RRN'],
                       palette=sns.light_palette('royalblue', n_colors=11, reverse=True)
                       )
#        sns.plt.ylim(0, 1000000)
        g.savefig('hybrid/%d_%d_%d_%d_%s_%d_%d_%s_%d_%s_%s_%.2f_%s.png' % (groupNum, routersPerGroup, nodesPerRouter, utilization, application, 
                                                            messageSize, messageIter, traceMode, traceNum, scheduler, routing, alpha, mode) )
    elif mode == '2d':
        normalize = True
        fs = 30
        figsizeX, figsizeY = 12, 12
        plt.rc('xtick', labelsize=fs)
        plt.rc('ytick', labelsize=fs)
        fig, ax = plt.subplots(1, 1, figsize=(figsizeX,figsizeY))
        fig.subplots_adjust(wspace=0, hspace=0)# remove the space between subplots.
        plt.title('Workload composed of two types of jobs (Workload %d)' % traceNum, fontsize=fs)

        colormap = {'Simple':'orangered','RRN':'dodgerblue','Hybrid':'forestgreen'
                    ,'RDG':'red','Slurm':'peru','RRR':'c','RDN':'blue'
                    }
        ax.patch.set_facecolor('white')
        if normalize:
            ax.set_xlabel('Avg. communication time of the small jobs (normalized)', fontsize=fs)
            ax.set_ylabel('Avg. communication time of the large jobs (normalized)', fontsize=fs)
        else:
            ax.set_xlabel('Avg. communication time of the small jobs (ms)', fontsize=fs)
            ax.set_ylabel('Avg. communication time of the large jobs (ms)', fontsize=fs)
        xnorm = dfThis[ (dfThis['Job sizes']<=16) & (dfThis['Allocation\nPolicy']=='Simple') ]['Avg. communication time (us)'].mean()
        ynorm = dfThis[ (dfThis['Job sizes']>16) & (dfThis['Allocation\nPolicy']=='Simple') ]['Avg. communication time (us)'].mean()
        xmin = min([dfThis[ (dfThis['Job sizes']<=16) & (dfThis['Allocation\nPolicy']==alloc) ]['Avg. communication time (us)'].mean() for alloc, color in colormap.items()])
        ymin = min([dfThis[ (dfThis['Job sizes']>16) & (dfThis['Allocation\nPolicy']==alloc) ]['Avg. communication time (us)'].mean() for alloc, color in colormap.items()])
        for alloc, color in colormap.items():
            x = dfThis[ (dfThis['Job sizes']<=16) & (dfThis['Allocation\nPolicy']==alloc) ]['Avg. communication time (us)'].mean()
            y = dfThis[ (dfThis['Job sizes']>16) & (dfThis['Allocation\nPolicy']==alloc) ]['Avg. communication time (us)'].mean()
            if normalize:
                ax.plot(x/xnorm, y/ynorm, '*' if alloc=='Hybrid' else 'o', color=color, markersize=25 if alloc=='Hybrid' else 20)
                ax.text(x/xnorm, y/ynorm, alloc, fontsize=fs)
                ax.set_xlim(0, 2)
                ax.set_ylim(0, 1.5)
                ax.set_yticks([0,0.5,1,1.5])
            else:
                ax.plot(x/1000, y/1000, '*' if alloc=='Hybrid' else 'o', color=color, markersize=25 if alloc=='Hybrid' else 20)
                ax.text(x/1000, y/1000, alloc, fontsize=fs)
                ax.set_xlim(0, xmin/1000*2)
                ax.set_ylim(0, ymin/1000*2)
        ax.grid(linestyle='--', color='black')
        rms = {58:'0.1', 59:'1', 60:'10', 61:'100'}
        ax.text(0.1, 1.3, 'Application: %s' % application, fontsize=fs)
        ax.text(0.1, 1.2, 'Ratio of message size (small jobs to large jobs): %s' % rms[traceNum], fontsize=fs)
        
        fig.tight_layout()
        name = 'hybrid/%s_%d_%d_%d_%d_%s_%d_%d_%s_%d_%s_%s_%.2f.png' % (mode, groupNum, routersPerGroup, nodesPerRouter, utilization, application, 
                                                                messageSize, messageIter, traceMode, traceNum, scheduler, routing, alpha)
        fig.savefig(name)
        plt.close()

def one1d(ax, df, mode, colormap, normalize, rowPara, irow, icol, fs, groupNum, routersPerGroup, nodesPerRouter, utilization, application, messageSize, messageIter, traceMode, traceNum, scheduler, routing, alpha):
    if messageSize == 100000 and application == 'fft':
        return
    nrow = len(rowPara)
    dfThis = df[
                (df['groupNum']==groupNum)
                & (df['routersPerGroup']==routersPerGroup)
                & (df['nodesPerRouter']==nodesPerRouter)
                & (df['utilization']==utilization)
                & (df['application']==application)
                & (df['messageSize']==messageSize)
                & (df['messageIter']==messageIter)
                & (df['traceMode']==traceMode)
                & (df['traceNum']==traceNum)
                & (df['scheduler']==scheduler)
                & (df['routing']==routing)
                & (df['alpha']==alpha)
                ].copy()

    # change the names for drawing.
    dfThis.replace('dflyhybrid','Hybrid',inplace=True)
    dfThis.replace('dflyhybridbf','Hybrid\n-BestFit',inplace=True)
    dfThis.replace('dflyhybridthres2','Hybrid\n-IncThres',inplace=True)
    dfThis.replace('dflyhybridrn','Hybrid\n-Random',inplace=True)
    dfThis.replace('dflyslurm','Slurm',inplace=True)
    dfThis.replace('simple','Simple',inplace=True)
    dfThis.replace('random','RDN',inplace=True)
    dfThis.replace('dflyrdr','RDR',inplace=True)
    dfThis.replace('dflyrdg','RDG',inplace=True)
    dfThis.replace('dflyrrn','RRN',inplace=True)
    dfThis.replace('dflyrrr','RRR',inplace=True)
    dfThis.rename(columns={'jobSize':'Job sizes'}, inplace=True)
    dfThis.rename(columns={'time(us)':'Avg. communication time (us)'}, inplace=True)
    dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)

    if irow == nrow - 1:
        ax[irow][icol].set_xlabel('Allocation Policies', fontsize=fs)
    if icol == 0:
        if normalize:
            ax[irow][icol].set_ylabel('Avg. communication time\n(normalized)', fontsize=fs)
        else:
            ax[irow][icol].set_ylabel('Avg. communication\ntime (ms)', fontsize=fs)
    ynorm = dfThis[ dfThis['Allocation\nPolicy']=='Simple' ]['Avg. communication time (us)'].mean()
    x = 0
    if normalize:
        ylim = 2 if traceNum == 66 else 6
    else:
        ylim = 2*ynorm/1000 if traceNum == 66 else 6*ynorm/1000
    for alloc in ['Hybrid','Simple','Slurm','RDG','RDR','RRR','RDN','RRN']:
        y = dfThis[ (dfThis['Allocation\nPolicy']==alloc) ]['Avg. communication time (us)'].mean()
        yerr = dfThis[ (dfThis['Allocation\nPolicy']==alloc) ]['Avg. communication time (us)'].std()
        if normalize:
            ax[irow][icol].bar(x, y/ynorm, yerr=yerr/ynorm, color=colormap[alloc], error_kw=dict(ecolor='gray', lw=5, capsize=10, capthick=4))
        else:
            ax[irow][icol].bar(x, y/1000, yerr=yerr/1000, color=colormap[alloc], error_kw=dict(ecolor='gray', lw=5, capsize=10, capthick=4))
#        ax[irow][icol].set_xlim(0, 2)
        ax[irow][icol].set_ylim(0, ylim)
#        ax[irow][icol].set_xticks([0,0.5,1,1.5])
#        ax[irow][icol].set_yticks([0,0.5,1,1.5])
        ax[irow][icol].axes.xaxis.set_ticklabels([])
        if normalize and icol != 0:
            ax[irow][icol].axes.yaxis.set_ticklabels([])
        x += 1
    ax[irow][icol].yaxis.grid(linestyle='--', color='black')
    ax[irow][icol].text(0.1, 0.85*ylim, '%s' % application, fontsize=fs+15)
    ax[irow][icol].text(0.1, 0.65*ylim, 'Bandwidth ratio of\n  global-to-local links: %.2f' % (rowPara[irow]['alpha']), fontsize=fs+4)
    ax[irow][icol].text(0.1, 0.55*ylim, 'Message size: %d KB' % (rowPara[irow]['mesSize']/1000), fontsize=fs+4)
    
#    if normalize:
#        patches = []
#        patches.append(mpatches.Patch(color='forestgreen', label='Hybrid'))
#        patches.append(mpatches.Patch(color='brown', label='Simple'))
#        patches.append(mpatches.Patch(color='red', label='Slurm'))
#        patches.append(mpatches.Patch(color='orange', label='RDG'))
#        patches.append(mpatches.Patch(color='c', label='RDR'))
#        patches.append(mpatches.Patch(color='dodgerblue', label='RRR'))
#        patches.append(mpatches.Patch(color='royalblue', label='RDN'))
#        patches.append(mpatches.Patch(color='blue', label='RRN'))
#        ax[irow][icol].legend(handles=patches, loc='upper left', fontsize=fs-6, ncol=4)

def one2d(ax, df, mode, colormap, normalize, rowPara, irow, icol, fs, groupNum, routersPerGroup, nodesPerRouter, utilization, application, messageSize, messageIter, traceMode, traceNum, scheduler, routing, alpha):
    if traceNum != 69 and application == 'fft':
        return
    nrow = len(rowPara)
    dfThis = df[
                (df['groupNum']==groupNum)
                & (df['routersPerGroup']==routersPerGroup)
                & (df['nodesPerRouter']==nodesPerRouter)
                & (df['utilization']==utilization)
                & (df['application']==application)
                & (df['messageSize']==messageSize)
                & (df['messageIter']==messageIter)
                & (df['traceMode']==traceMode)
                & (df['traceNum']==traceNum)
                & (df['scheduler']==scheduler)
                & (df['routing']==routing)
                & (df['alpha']==alpha)
                ].copy()

    # change the names for drawing.
    dfThis.replace('dflyhybrid','Hybrid',inplace=True)
    dfThis.replace('dflyhybridbf','Hybrid\n-BestFit',inplace=True)
    dfThis.replace('dflyhybridthres2','Hybrid\n-IncThres',inplace=True)
    dfThis.replace('dflyhybridrn','Hybrid\n-Random',inplace=True)
    dfThis.replace('dflyslurm','Slurm',inplace=True)
    dfThis.replace('simple','Simple',inplace=True)
    dfThis.replace('random','RDN',inplace=True)
    dfThis.replace('dflyrdr','RDR',inplace=True)
    dfThis.replace('dflyrdg','RDG',inplace=True)
    dfThis.replace('dflyrrn','RRN',inplace=True)
    dfThis.replace('dflyrrr','RRR',inplace=True)
    dfThis.rename(columns={'jobSize':'Job sizes'}, inplace=True)
    dfThis.rename(columns={'time(us)':'Avg. communication time (us)'}, inplace=True)
    dfThis.rename(columns={'allocation':'Allocation\nPolicy'}, inplace=True)

    if normalize:
        if irow == nrow - 1:
            ax[irow][icol].set_xlabel('Avg. communication time of\nthe small jobs (normalized)', fontsize=fs-2)
        if icol == 0:
            ax[irow][icol].set_ylabel('Avg. communication time of\nthe large jobs (normalized)', fontsize=fs-2)
        xnorm = dfThis[ (dfThis['Job sizes']<=16) & (dfThis['Allocation\nPolicy']=='Simple') ]['Avg. communication time (us)'].mean()
        ynorm = dfThis[ (dfThis['Job sizes']>16) & (dfThis['Allocation\nPolicy']=='Simple') ]['Avg. communication time (us)'].mean()
    else:
        if irow == nrow - 1:
            ax[irow][icol].set_xlabel('Avg. communication time of\nthe small jobs (ms)', fontsize=fs)
        if icol == 0:
            ax[irow][icol].set_ylabel('Avg. communication time of\nthe large jobs (ms)', fontsize=fs)
        xmin = min([dfThis[ (dfThis['Job sizes']<=16) & (dfThis['Allocation\nPolicy']==alloc) ]['Avg. communication time (us)'].mean() for alloc, color in colormap.items()])
        ymin = min([dfThis[ (dfThis['Job sizes']>16) & (dfThis['Allocation\nPolicy']==alloc) ]['Avg. communication time (us)'].mean() for alloc, color in colormap.items()])
    for alloc, color in colormap.items():
        dfAlloc = dfThis[ (dfThis['Allocation\nPolicy']==alloc) ]
        if len(dfAlloc) == 0:
            pass#print('missing results: %s' % alloc)
        x = dfAlloc[ (dfAlloc['Job sizes']<=16) ]['Avg. communication time (us)'].mean()
        y = dfAlloc[ (dfAlloc['Job sizes']>16) ]['Avg. communication time (us)'].mean()
        if normalize:
            if alloc == 'Hybrid':
                ax[irow][icol].plot(x/xnorm, y/ynorm, '*', color=color, markersize=40)
            elif alloc in ['Simple','RDG','Slurm']:
                ax[irow][icol].plot(x/xnorm, y/ynorm, 'd', color=color, markersize=30)
            elif alloc in ['RDN','RDR','RRN','RRR']:
                ax[irow][icol].plot(x/xnorm, y/ynorm, 'o', color=color, markersize=30)
            #ax[irow][icol].text(x/xnorm, y/ynorm, alloc, fontsize=15)
            ax[irow][icol].set_xlim(0, 4)
            ylim = 2
            ax[irow][icol].set_ylim(0, ylim)
            ax[irow][icol].set_xticks([0,1,2,3,4])
#            ax[irow][icol].set_yticks([0,0.5,1,1.5])
            if irow != nrow - 1:
                ax[irow][icol].axes.xaxis.set_ticklabels([])
            if icol != 0:
                ax[irow][icol].axes.yaxis.set_ticklabels([])
        else:
            ax[irow][icol].plot(x/1000, y/1000, '*' if alloc=='Hybrid' else 'o', color=color, markersize=40 if alloc=='Hybrid' else 30)
            #ax[irow][icol].text(x/1000, y/1000, alloc, fontsize=fs)
#            ax[irow][icol].set_xlim(0, xmin/1000*2)
#            ax[irow][icol].set_ylim(0, ymin/1000*2)
    ax[irow][icol].grid(linestyle='--', color='black')
    
    ax[irow][icol].text(0.1, 0.85*ylim, '%s' % application, fontsize=fs+15)
#    ax[irow][icol].text(0.1, 0.05*ylim, 'Bandwidth ratio of\n  global-to-local links: %.2f' % (rowPara[irow]['alpha']), fontsize=fs+4)
    ax[irow][icol].text(0.1, 0.25*ylim, 'machine utilization: %d%%' % (rowPara[irow]['uti']), fontsize=fs)
    ax[irow][icol].text(0.1, 0.15*ylim, 'small jobs message size: %d KB' % (rowPara[irow]['smallSize']), fontsize=fs)
    ax[irow][icol].text(0.1, 0.05*ylim, 'large jobs message size: %d KB' % (rowPara[irow]['largeSize']), fontsize=fs)
    
def multi2d(df, alpha):
    normalize = True
    fs = 22
    apps = list(set(df['application']))
    apps.sort()
#    rowPara = {0:{'p':4, 'a':4, 'g':9},
#            1:{'p':4, 'a':4, 'g':17},
#            2:{'p':4, 'a':6, 'g':25},
#            3:{'p':4, 'a':8, 'g':33},
#            4:{'p':4, 'a':10, 'g':41}
#            }
#    rowPara = {0:{'trace':58, 'ratio':'0.1'},
#                    1:{'trace':59, 'ratio':'1'},
#                    2:{'trace':60, 'ratio':'10'},
#                    3:{'trace':61, 'ratio':'100'},
#                    }
#    rowPara = {0:{'uti':20},
#               1:{'uti':40},
#                2:{'uti':60},
#                3:{'uti':80},
#                4:{'uti':100},}
#    rowPara = {0:{'alpha':0.1},
#               1:{'alpha':0.25},
#                2:{'alpha':1},
#                3:{'alpha':4},
#                4:{'alpha':10},}
#    rowPara = {0:{'p':4, 'a':4, 'g':9},
#            1:{'p':4, 'a':4, 'g':17},
#            2:{'p':4, 'a':4, 'g':25},
#            3:{'p':4, 'a':4, 'g':33},
#            4:{'p':4, 'a':4, 'g':41}}
#    rowPara = {0:{'alpha':0.25, 'uti':70, 'trace':69},
#               1:{'alpha':1, 'uti':70, 'trace':69},
#               2:{'alpha':4, 'uti':70, 'trace':69},
#               3:{'alpha':0.25, 'uti':90, 'trace':69},
#               4:{'alpha':1, 'uti':90, 'trace':69},
#               5:{'alpha':4, 'uti':90, 'trace':69}}
#    rowPara = {0:{'trace':69,'smallSize':1,'largeSize':1},
#               1:{'trace':70,'smallSize':100,'largeSize':100},
#               2:{'trace':71,'smallSize':100,'largeSize':1},
#               3:{'trace':72,'smallSize':1,'largeSize':100}}
    rowPara = {0:{'trace':69,'smallSize':1,'largeSize':1, 'uti':90},
               1:{'trace':70,'smallSize':100,'largeSize':100, 'uti':90},
               2:{'trace':71,'smallSize':100,'largeSize':1, 'uti':90},
               3:{'trace':72,'smallSize':1,'largeSize':100, 'uti':90},
               4:{'trace':69,'smallSize':1,'largeSize':1, 'uti':70},
               5:{'trace':70,'smallSize':100,'largeSize':100, 'uti':70},
               6:{'trace':71,'smallSize':100,'largeSize':1, 'uti':70},
               7:{'trace':72,'smallSize':1,'largeSize':100, 'uti':70}}
#    rowPara = {0:{'alpha':0.25},
#               1:{'alpha':1},
#               2:{'alpha':4}}

    nrow = len(rowPara)
    figsizeX, figsizeY = 5*len(apps)+5, 5*len(rowPara)
    
    plt.rc('xtick', labelsize=fs)
    plt.rc('ytick', labelsize=fs)
    fig, ax = plt.subplots(nrow, len(apps), figsize=(figsizeX,figsizeY))
    fig.subplots_adjust(wspace=0, hspace=0)# remove the space between subplots.
    #plt.title('Workload composed of two types of jobs (Workload %d)' % 69, fontsize=fs)

    colormap = {'Simple':'brown','Slurm':'red','RDG':'orange','Hybrid':'forestgreen'
                ,'RDR':'c','RRR':'dodgerblue','RDN':'royalblue','RRN':'blue'
                }
    patches = []
    labels = ['Hybrid','Simple','Slurm','RDG','RDR','RRR','RDN','RRN']
    patches.append(mpatches.Patch(color='forestgreen', label='Hybrid'))
    patches.append(mpatches.Patch(color='brown', label='Simple'))
    patches.append(mpatches.Patch(color='red', label='Slurm'))
    patches.append(mpatches.Patch(color='orange', label='RDG'))
    patches.append(mpatches.Patch(color='c', label='RDR'))
    patches.append(mpatches.Patch(color='dodgerblue', label='RRR'))
    patches.append(mpatches.Patch(color='royalblue', label='RDN'))
    patches.append(mpatches.Patch(color='blue', label='RRN'))
    lgd = fig.legend(handles=patches, labels=labels, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=fs+20, ncol=1)

    for irow in range(nrow):
        for icol in range(len(apps)):
#            one2d(ax, df, '2d', colormap, normalize, rowPara, irow, icol, fs, groupNum=17, nodesPerRouter=4, routersPerGroup=4,
#                  utilization=rowPara[irow]['uti'], application=apps[icol], messageSize=1000, messageIter=1, traceMode='corner',
#                  traceNum=72, scheduler='easy', routing='adaptive', alpha=rowPara[irow]['alpha'])                    
            one2d(ax, df, '2d', colormap, normalize, rowPara, irow, icol, fs, groupNum=65, nodesPerRouter=4, routersPerGroup=8,
                  utilization=rowPara[irow]['uti'], application=apps[icol], messageSize=1000, messageIter=1, traceMode='corner',
                  traceNum=rowPara[irow]['trace'], scheduler='easy', routing='adaptive', alpha=alpha)                    
#            one2d(ax, df, '2d', colormap, normalize, rowPara, irow, icol, fs, groupNum=17, nodesPerRouter=4, routersPerGroup=4,
#                  utilization=90, application=apps[icol], messageSize=1000, messageIter=1, traceMode='corner',
#                  traceNum=69, scheduler='easy', routing='adaptive', alpha=rowPara[irow]['alpha'])                    
                    
    fig.tight_layout()
    name = 'hybrid/hete_4nodesPerRouter_8routersPerGroup_65group_bandwidthRatio%.2f.png' % alpha
    fig.savefig(name, bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.close()

def multi1d(df, traceNum, uti):
    normalize = True
    fs = 24
    apps = list(set(df['application']))
    apps.sort()
    rowPara = {0:{'alpha':0.25, 'mesSize':1000},
               1:{'alpha':1, 'mesSize':1000},
               2:{'alpha':4, 'mesSize':1000},
               3:{'alpha':0.25, 'mesSize':100000},
               4:{'alpha':1, 'mesSize':100000},
               5:{'alpha':4, 'mesSize':100000}}
#    rowPara = {0:{'alpha':0.25},
#               1:{'alpha':1},
#               2:{'alpha':4}}
              
    nrow = len(rowPara)
    figsizeX, figsizeY = 5*len(apps)+5, 5*len(rowPara)
    
    plt.rc('xtick', labelsize=fs)
    plt.rc('ytick', labelsize=fs)
    fig, ax = plt.subplots(nrow, len(apps), figsize=(figsizeX,figsizeY))
    fig.subplots_adjust(wspace=0, hspace=0)# remove the space between subplots.

    colormap = {'Simple':'brown','Slurm':'red','RDG':'orange','Hybrid':'forestgreen'
                ,'RDR':'c','RRR':'dodgerblue','RDN':'royalblue','RRN':'blue'
                }
    patches = []
    labels = ['Hybrid','Simple','Slurm','RDG','RDR','RRR','RDN','RRN']
    patches.append(mpatches.Patch(color='forestgreen', label='Hybrid'))
    patches.append(mpatches.Patch(color='brown', label='Simple'))
    patches.append(mpatches.Patch(color='red', label='Slurm'))
    patches.append(mpatches.Patch(color='orange', label='RDG'))
    patches.append(mpatches.Patch(color='c', label='RDR'))
    patches.append(mpatches.Patch(color='dodgerblue', label='RRR'))
    patches.append(mpatches.Patch(color='royalblue', label='RDN'))
    patches.append(mpatches.Patch(color='blue', label='RRN'))
    lgd = fig.legend(handles=patches, labels=labels, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=fs+20, ncol=1)
    
    for irow in range(nrow):
        for icol in range(len(apps)):
            one1d(ax, df, '1d', colormap, normalize, rowPara, irow, icol, fs, groupNum=65, nodesPerRouter=4, routersPerGroup=8,
                  utilization=uti, application=apps[icol], messageSize=rowPara[irow]['mesSize'], messageIter=1, traceMode='corner',
                  traceNum=traceNum, scheduler='easy', routing='adaptive', alpha=rowPara[irow]['alpha'])                    
    fig.tight_layout()
    name = 'hybrid/homo_4nodesPerRouter_8routersPerGroup_65group_1KmessageSize_%dutilization_%dnodeJobs.png' % (uti, 16 if traceNum==64 else 64)
    fig.savefig(name, bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.close()

#=====================================================
# new graphs for paper editing.
def main():
    import datetime
    now = datetime.datetime.now()

#    df = pd.read_csv('hybrid/isolated.csv')
#    for i in range(58, 62):
#        twoSizeJobs(df, '2d', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=100, application='alltoall', messageSize=1000, messageIter=10, 
#                    traceMode='corner', traceNum=i, scheduler='easy', routing='adaptive', alpha=1)


#    df = pd.read_csv('hybrid/machine_4_8_65.csv')
#    df.replace('stencil','halo3d',inplace=True)
#    multi1d(df, 64, 90)
#    multi1d(df, 64, 70)
#    multi1d(df, 66, 90)
#    multi1d(df, 66, 70)

    df = pd.read_csv('hybrid/machine_4_8_65.csv')
    df.replace('stencil','halo3d',inplace=True)
    multi2d(df, 0.25)
    multi2d(df, 1)
    multi2d(df, 4)

#    dfs = []
#    for application in ['halo2d','fft','stencil','bcast','halo3d26','alltoall']:
#        for allocation in ['simple', 'random', 'dflyrdr', 'dflyrdg', 'dflyrrn', 'dflyrrr', 'dflyslurm', 'dflyhybrid']:
#            dfs.append(pd.read_csv('hybrid/machine_4_8_65/machine_4_8_65_%s_%s.csv' % (allocation, application)))
#    df = pd.concat(dfs, ignore_index=True)
#    df.to_csv('hybrid/machine_4_8_65.csv', index=False)

#================================
# obsolete
#df = pd.read_csv('hybrid/hybrid.csv')
#draw(df, 'motivation', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=100, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)

# obsolete

#df = pd.read_csv('hybrid/hybrid.csv')
#draw(df, 'mixMessageSize', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)

# obsolete
#df = pd.read_csv('hybrid/hybrid.csv')
#draw(df, 'normalCorner', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=0.25)
#draw(df, 'normalCorner', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=4)
#draw(df, 'normalCorner', groupNum=33, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)
#draw(df, 'normalCorner', groupNum=9, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)
#draw(df, 'normalCorner', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=100, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)
#draw(df, 'normalCorner', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=50, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)
#draw(df, 'normalCorner', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=1000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)

#df = pd.read_csv('hybrid/hybrid.csv')
#draw(df, 'normalSum', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)

#df1 = pd.read_csv('hybrid/hybrid_random.csv')
#df2 = pd.read_csv('hybrid/random2.csv')
#df = pd.concat([df1, df2], ignore_index=True)
#draw(df2, 'compHybrid', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='random', scheduler='easy', routing='adaptive', alpha=1)


#============================================

# graphs for the SC paper.

#df = pd.read_csv('hybrid/hybrid_random.csv')
#draw(df, 'normal', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='random', scheduler='easy', routing='adaptive', alpha=1)
#
#df = pd.read_csv('hybrid/hybrid_random.csv')
#draw(df, 'normalSum', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='random', scheduler='easy', routing='adaptive', alpha=1)
#
#df1 = pd.read_csv('hybrid/hybrid.csv')
#df2 = pd.read_csv('hybrid/hybrid2.csv')
#df = pd.concat([df1, df2], ignore_index=True)
#draw(df, 'normalCorner', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)
#
#
#
#df1 = pd.read_csv('hybrid/hybrid_random.csv')
#df2 = pd.read_csv('hybrid/random2.csv')
#df = pd.concat([df1, df2], ignore_index=True)
#draw(df, 'SumComp', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='random', scheduler='easy', routing='adaptive', alpha=1)
#
#df1 = pd.read_csv('hybrid/hybrid.csv')
#df2 = pd.read_csv('hybrid/hybrid2.csv')
#df = pd.concat([df1, df2], ignore_index=True)
#draw(df, 'compHybrid', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)
#
#df = pd.read_csv('hybrid/hybrid_order.csv')
#simpleDraw(df, 'compOrder', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='random', scheduler='easy', routing='adaptive', alpha=1)
#
#df = pd.read_csv('hybrid/motivation.csv')
#motivation(df, 'motivation2', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=100, application='alltoall', messageSize=1000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)
#
#df = pd.read_csv('hybrid/hybrid.csv')
#draw(df, 'order1', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=100, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)

#df = pd.read_csv('hybrid/hybrid.csv')
#draw(df, 'order2', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=100, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)
#
#dfStat1 = pd.read_csv('hybrid/statistics.csv')
#dfStat2 = pd.read_csv('hybrid/statistics2.csv')
#dfStat = pd.concat([dfStat1, dfStat2], ignore_index=True)
#statDraw(dfStat, 'corner', 'global', 'send_packet_count')
#statDraw(dfStat, 'corner', 'local', 'send_packet_count')
#statDraw(dfStat, 'corner', 'global', 'output_port_stalls')
#statDraw(dfStat, 'corner', 'local', 'output_port_stalls')
#
#
#small = pd.read_csv('hybrid/APS_corner7_size4.csv')
#large = pd.read_csv('hybrid/APS_corner7_size32.csv')
#separate(small, large, groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)
#
#df1 = pd.read_csv('hybrid/hybrid_random.csv')
#df2 = pd.read_csv('hybrid/hybrid_randomChangePara.csv')
#df = pd.concat([df1, df2], ignore_index=True)
#comparePara(df, 'pattern')
#comparePara(df, 'machine')
#comparePara(df, 'messageSize')
#comparePara(df, 'utilization')
#comparePara(df, 'alpha')

#============================================
#df = pd.read_csv('hybrid/Optimum.csv')
#draw(df, 'optimum', groupNum=9, routersPerGroup=4, nodesPerRouter=2, utilization=100, application='alltoall', messageSize=1000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)

#df = pd.read_csv('hybrid/Optimum21.csv')
#draw(df, 'optimum21', groupNum=9, routersPerGroup=4, nodesPerRouter=2, utilization=100, application='alltoall', messageSize=1000, messageIter=10, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)

#df = pd.read_csv('hybrid/largeMachine.csv')
#draw(df, 'normalSum', groupNum=21, routersPerGroup=5, nodesPerRouter=5, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='random', scheduler='easy', routing='adaptive', alpha=1)
#
#df = pd.read_csv('hybrid/largeMachine.csv')
#draw(df, 'normal', groupNum=21, routersPerGroup=5, nodesPerRouter=5, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='random', scheduler='easy', routing='adaptive', alpha=1)

#df = pd.read_csv('hybrid/hybrid.csv')
#draw(df, 'mixIter', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=100000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)

#df = pd.read_csv('hybrid/mixIterOld.csv')
#df = pd.read_csv('hybrid/mixIter.csv')
#draw(df, 'mixIterRaw', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=100, application='alltoall', messageSize=1000, messageIter=1, 
#                traceMode='corner', scheduler='easy', routing='adaptive', alpha=1)

#df1 = pd.read_csv('hybrid/more_stencil.csv')
#df2 = pd.read_csv('hybrid/more_alltoall.csv')
#df3 = pd.read_csv('hybrid/more_bcast.csv')
#df3 = pd.read_csv('hybrid/more_halo3d26.csv')
#df = pd.concat([df1, df2, df3], ignore_index=True)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='bcast', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=22, scheduler='easy', routing='adaptive', alpha=1)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='bcast', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=26, scheduler='easy', routing='adaptive', alpha=1)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='bcast', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=27, scheduler='easy', routing='adaptive', alpha=1)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=22, scheduler='easy', routing='adaptive', alpha=1)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=26, scheduler='easy', routing='adaptive', alpha=1)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='alltoall', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=27, scheduler='easy', routing='adaptive', alpha=1)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='stencil', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=22, scheduler='easy', routing='adaptive', alpha=1)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='stencil', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=26, scheduler='easy', routing='adaptive', alpha=1)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='stencil', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=27, scheduler='easy', routing='adaptive', alpha=1)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='halo3d26', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=22, scheduler='easy', routing='adaptive', alpha=1)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='halo3d26', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=26, scheduler='easy', routing='adaptive', alpha=1)
#twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=75, application='halo3d26', messageSize=1000, messageIter=1, 
#                traceMode='corner', traceNum=27, scheduler='easy', routing='adaptive', alpha=1)

#dfStat = pd.read_csv('hybrid/more_bcast_stat.csv')
#statDraw(dfStat, 'corner', 'global', 'send_packet_count')
#statDraw(dfStat, 'corner', 'local', 'send_packet_count')
#statDraw(dfStat, 'corner', 'global', 'output_port_stalls')
#statDraw(dfStat, 'corner', 'local', 'output_port_stalls')

#df = pd.read_csv('hybrid/allsmallRandom.csv')
#for i in range(42, 51):
#    twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=100, application='alltoall', messageSize=1000, messageIter=1, 
#                    traceMode='corner', traceNum=i, scheduler='easy', routing='adaptive', alpha=1)

#df = pd.read_csv('hybrid/powerTwo.csv')
#for i in [100+i*10+j for i in range(1, 8) for j in range(i+1, 8)]:
#    twoSizeJobs(df, 'asdf', groupNum=17, routersPerGroup=4, nodesPerRouter=4, utilization=100, application='alltoall', messageSize=1000, messageIter=1, 
#                    traceMode='corner', traceNum=i, scheduler='easy', routing='adaptive', alpha=1)

    print('finished in %d seconds.' % (datetime.datetime.now()-now).seconds)


if __name__ == '__main__':
    main()
