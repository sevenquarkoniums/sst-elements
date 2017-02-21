#!/usr/bin/env python
'''
Date        : 07/17/2015  
Created by  : Fulya Kaplan, edited by Yijia.
Description : This sub-python script parses the snapshot xml file that is dumped by the scheduler. 
It then creates a runscript for ember simulation and runs the script. 
Created specifically for detailed simulation of network congestion together with scheduling & application task mapping algorithms.

### TODO ###
1 can delete myloadfile lines.
'''
useMyLoadfile = False# name: myloadfile.

import os, sys
from xml.dom.minidom import parse
import xml.dom.minidom

from optparse import OptionParser
import math
import numpy as np
import random


class Time:
    def __init__(self):
        self.snapshotTime     = -1
        self.nextArrivalTime  = -1

    def set(self, snapshotTime, nextArrivalTime):
        self.snapshotTime     = snapshotTime
        self.nextArrivalTime  = nextArrivalTime

class Job:
    def __init__(self):
        self.jobNum        = -1
        self.nodeList      = []
        self.numNodes      = -1
        self.numCores      = -1
        self.motifFile     = ''
        self.startingMotif = -1

    def set(self, jobNum, nodeList, motifFile, startingMotif):
        self.jobNum        = jobNum
        self.nodeList      = nodeList
        self.numNodes      = len(nodeList)
        self.numCores      = len(nodeList[0][1])
        self.motifFile     = motifFile
        self.startingMotif = startingMotif


# Function to run linux commands
def run(cmd):
    #print(cmd)
    os.system(cmd)

# Parser for the xml file that holds the snapshot from the scheduler
def parse_xml (options):

    fileName = options.xmlFile
    # Open XML document using minidom parser
    DOMTree = xml.dom.minidom.parse(fileName)
    snapshot = DOMTree.documentElement

    # Get all times and jobs in the snapshot
    time = snapshot.getElementsByTagName("time")
    jobs  = snapshot.getElementsByTagName("job")

    # Create a Time object and populate
    TimeObject = Time()

    snapshotTime_ = time[0].getElementsByTagName('snapshotTime')[0]
    snapshotTime  = int(snapshotTime_.childNodes[0].data)
    print
    print "snapshotTime: %d" % snapshotTime
    nextArrivalTime_ = time[0].getElementsByTagName('nextArrivalTime')[0]
    nextArrivalTime  = int(nextArrivalTime_.childNodes[0].data)
    print "nextArrivalTime: %d" % nextArrivalTime

    TimeObject.set(snapshotTime, nextArrivalTime)
    # end

    # Create a list of Job objects and populate
    JobObjects = []

    print "***Currently Running Jobs***"
    for job in jobs:
        if job.hasAttribute("number"):
            jobNum = int(job.getAttribute("number"))
            print "Job Number: %d" % jobNum

        motifFile_ = job.getElementsByTagName('motifFile')[0]
        motifFile  = str(motifFile_.childNodes[0].data)
        #print "motifFile: %s" % motifFile

        startingMotif_ = job.getElementsByTagName('startingMotif')[0]
        startingMotif  = int(startingMotif_.childNodes[0].data)
        #print "startingMotif: %d" % startingMotif

        nodes = job.getElementsByTagName('node')
        NodeList = []
        #NodeList = [[0, []] for i in range(nodes.length)]
        #print nodes[0].childNodes[1].childNodes[0].data
        for node in nodes:
            nodeID = int(node.getAttribute("number"))
            #print "Node: %d" % nodeID

            tasks_ = node.getElementsByTagName('tasks')[0]
            tasks  = str(tasks_.childNodes[0].data)
            #print "TaskList string: %s" % tasksStr
            tasks  = tasks.split(',')
            #print tasksStr

            temp = [nodeID, []]
            for i in range(len(tasks) - 1):
                temp[1].append(int(tasks[i]))
            NodeList.append(temp)
        #print NodeList
        if options.shuffle == True:
            random.shuffle(NodeList)

        # Find number of cores per node
        numCores = len(NodeList[0][1])

        # Sort NodeList to match the desired mapping in ember
        #Fulya Jan 2016: Commented out sorting, fix later
        #sortedNodeList = sort_NID(NodeList, numCores)
        sortedNodeList = NodeList

        tempJobObject = Job()
        tempJobObject.set(jobNum, sortedNodeList, motifFile, startingMotif)
        JobObjects.append(tempJobObject)
    #end
    
    return (TimeObject, JobObjects)

def sort_NID (nodeList, numCores):

    sorted_nodeList = [[] for i in range(len(nodeList))]

    for node in nodeList:
        index = node[1][0] / numCores
        sorted_nodeList[index] = node
        #print "First Task Num: %s Index: %s" % (node[1][0], index)
        #print sorted_nodeList[index]

    return (sorted_nodeList)

# Generates necessary files for ember to run
def generate_ember_files (TimeObject, JobObjects, options):

    output_folder = os.getenv('SIMOUTPUT')
    if output_folder == None:
        options.output_folder = "./"
    else:
        options.output_folder = output_folder

    loadfile    = generate_loadfile (TimeObject, JobObjects, options)
    mapfile     = generate_mapfile (JobObjects, options)
    execcommand = generate_ember_script (TimeObject, JobObjects, loadfile, mapfile, options)

    return (execcommand)

# Generates a loadfile for ember
def generate_loadfile (TimeObject, JobObjects, options):

    loadfile  = options.output_folder + "loadfile"
    # Open loadfile to write 
    ldfile = open(loadfile, "w")

    # Keywords used in the loadfile format
    J_KEY = "[JOB_ID] "
    N_KEY = "[NID_LIST] "
    M_KEY = "[MOTIF] "

    # Populate loadfile with the job & nodeID & motif info 
    for Job in JobObjects:
        ldfile_str = ""

        # Insert Job Number
        ldfile_str += J_KEY + str(Job.jobNum) + "\n\n"

        # Insert Sorted NodeID List
        ldfile_str += N_KEY
        for nodelist in Job.nodeList:
            if(nodelist == Job.nodeList[-1]):
                ldfile_str += str(nodelist[0]) + "\n"
            else:
                ldfile_str += str(nodelist[0]) + ","

        # Insert Motifs from the motifFile
        mFile = open(Job.motifFile, "r")
        mFile_str = mFile.readlines()

        if (Job.startingMotif != 0):
            ldfile_str += M_KEY + "Init\n"

        for motifNum in range(Job.startingMotif, len(mFile_str)):
            if (mFile_str[motifNum] != "\n"):
                ldfile_str += M_KEY + mFile_str[motifNum]
        mFile.close()

        ldfile_str += "\n"

        # Write this job's info to the loadfile
        ldfile.writelines(ldfile_str)
    ldfile.close()

    return (loadfile)

def generate_mapfile (JobObjects, options):

    mapfile = options.output_folder + "mapFile.txt"
    # Open mapfile to write 
    mpfile = open(mapfile, "w")

    # Populate mapfile with the job & nodeID & motif info 
    for Job in JobObjects:
        mpfile_str = ""

        # Insert Job Start Identifier
        mpfile_str += "[JOB " + str(Job.jobNum) + " START]\n"

        # Insert Task List for Each Node
        for nodelist in Job.nodeList:
            tasklist = nodelist[1]

            for task in tasklist:
                if(task == tasklist[-1]):
                    mpfile_str += str(task) + "\n"
                else:
                    mpfile_str += str(task) + " "

        # Insert Job End Identifier
        mpfile_str += "[JOB " + str(Job.jobNum) + " END]\n"

        # Write this job's task map info to the mapfile
        mpfile.writelines(mpfile_str)
    mpfile.close()

    return (mapfile)

# Generates a script for ember to run
def generate_ember_script (TimeObject, JobObjects, loadfile, mapfile, options):
    
    emberLoad = "emberLoad.py"
    #currDir   = os.getcwd()

    if options.alpha == None:
        global_bw = "1"
        netBW = "1"
    else:
        global_bw = options.alpha
        if float(options.alpha) < 1:
            netBW = "1"
        else:
            netBW = options.alpha
    print netBW

    # If nextArrivalTime is zero, it means there are no other jobs left to arrive in the future. Do not use stop-at option.
    if TimeObject.nextArrivalTime == 0:
        execcommand = "sst "
    # Ember simulation will start from time zero, so feed it the relative time
    else:
        StopAtTime_ = TimeObject.nextArrivalTime - TimeObject.snapshotTime
        StopAtTime  = str(StopAtTime_) + "us"
        execcommand = "sst --stop-at " + StopAtTime
    # Generate commandline string to execute
    #execcommand += " --model-options=\"--topo=torus --shape=2x2x2 --numCores=1 --netFlitSize=8B --netPktSize=1024B --emberVerbose=0 --debug=0"
    execcommand += " --model-options=\"--topo=dragonfly2 --shape=%s --routingAlg=%s --numCores=2 --netFlitSize=8B --netPktSize=1024B --emberVerbose=0 --debug=0" % (options.dflyShape, options.routing)
        # dragonfly2 has different link arrangements.
    execcommand += " --host_bw=1GB/s --group_bw=1GB/s --global_bw=%sGB/s --netBW=%sGB/s" %(global_bw, netBW)
    execcommand += " --embermotifLog=" + options.output_folder + "motif"
    if options.rankmapper == "custom":
        execcommand += " --rankmapper=ember.CustomMap"
    else:
        execcommand += " --rankmapper=ember.LinearMap"
    execcommand += " --mapFile=" + mapfile
    execcommand += " --networkStatOut=" + options.output_folder + "networkStats.csv"
    if useMyLoadfile == False:
        execcommand += " --loadFile=" + loadfile + "\""
    else:
        execcommand += " --loadFile=" + options.output_folder + 'myloadfile' + "\""
    execcommand += " " + emberLoad + "\n"

    print execcommand

    return (execcommand)

# Gets a commandline string, puts it into a shell file and runs
def run_ember (execcommand):

    run(execcommand)

def main():

    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option("--xml",  action='store', dest="xmlFile", help="Name of the xml file that holds the current scheduler snapshot.") 
    parser.add_option("--alpha",  action='store', dest="alpha", help="Alpha = Global_link_BW / Local_link_BW.") 
    parser.add_option("--link_arrangement",  action='store', dest="link_arrangement", help="Global link arrangement for dragonfly.") 
    parser.add_option("--routing",  action='store', dest="routing", help="Routing algorithm.") 
    parser.add_option("--rankmapper",  action='store', dest="rankmapper", help="Custom or linear mapping.") 
    parser.add_option("--shuffle",  action='store_true', dest="shuffle", help="Random shuffling of the node list order.") 
    parser.add_option("--dflyShape",  action='store', dest="dflyShape", help="the shape parameter for dragonfly2 machine.")

    (options, args) = parser.parse_args()
    
    TimeObject, JobObjects = parse_xml (options = options)
    execcommand = generate_ember_files (TimeObject, JobObjects, options)
    run_ember (execcommand)

if __name__ == '__main__':
    main()
