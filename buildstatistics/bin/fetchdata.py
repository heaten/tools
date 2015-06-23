#!/usr/bin/env python2.7
import os
import sys
import pickle
import argparse
import json

path = '/proj/sgsn-tools/gtt_faults_trend/'
filename = 'gtt_ng_lsv_results'

def fetch_data():
    list = []
    datelist = []
    data = []
    with open(path+filename, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    for i in data:
        #print i
        date = i["time"]
        new = i["with_tr"]+i["unstable"]
        #print new
        #print date
        #print '='*100
        datelist.append(date)
        list.append(new)
#    print list    
#    print len(list)
#    print datelist
#    print len(datelist)
    return list

def main():
    fetch_data()

if __name__ == "__main__":
    main()
