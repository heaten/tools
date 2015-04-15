#! /usr/bin/env python2.7
import os
import sys
import pickle


x = 1
weekn = 23

def read_data(weeklist):
    list = []
    for n in weeklist:
        filename = 'w'+'%s'%n+'.txt'
        ft = open(filename,'r')
        data = pickle.load(ft)
        ft.close()
        list = list+data
    return list

def analysis_list(delta_l,raw_l):
    sum = 0
    for d in delta_l:
        times = raw_l.count(d)
        if times > x:
            print '*'*30
            print d
            print 'Failure time is %s'%times
            sum= sum+1
    print sum        

def main():
    # Read the legacy record
    oldlist = read_data([18,19,20,22])
    # Read the latest record
    newlist = read_data([weekn])
    
    # Remove duplicated case
    oldset = set(oldlist)
    newset = set(newlist)
    print len(oldset)
    print len(newset)
    
    # Get the new failed case set
    delta = newset - oldset
    #print delta
    print len(delta)
    
    # Print details info
    analysis_list(list(delta),list(newlist))

if __name__ == "__main__":
    main()
