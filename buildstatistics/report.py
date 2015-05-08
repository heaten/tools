#!/proj/sgsn-tools/wh/bin/sgenv python
import os
import sys
import pickle
import bs
from bs import BuildResult
import argparse

#Globe
x = 1
weekn = 27
path = '/home/ewwglli/tools/buildstatistics/'

def read_data(weeklist):
    list = []
    for n in weeklist:
        filename = 'w'+'%s'%n+'.txt'
        ft = open(path+filename,'r')
        data = pickle.load(ft)
        ft.close()
        list = list+data
    return list

def analysis_list(delta_l,raw_l):
    sum = 0
    total =0
    for d in delta_l:
        times = raw_l.count(d)
        if times >x:
            print '*'*30
            print d
            print 'Failure time is %s'%times
            sum= sum+1
            total = total + times
    print 'The number of new unstable case is %s'%sum        
    #print 'The total failure time for new case  is %s'%total        

def daily_report():
    filename = 'FailNumber.txt'    
    ft = open(path+filename,'r')
    data = pickle.load(ft)
    ft.close()
    list =[]
    for d in data:
        print d.id
        print d.number
        list.append(d.number)
    print 'The whole record is: %s'%list
    list10 = list[-10:]
    print 'The latest 10 record is: %s'%list10
    list10.sort(key = int)
    print 'The sorted 10 record is: %s'%list10

def weekly_report():
    # Read the legacy record
    oldlist = read_data([23,24,25,26])
    # Read the latest record
    newlist = read_data([27])
    
    # Remove duplicated case
    oldset = set(oldlist)
    newset = set(newlist)
    print ('Total failure times for last 4 weeks',':',len(oldlist))
    print ('Total failure times for this week',':',len(newlist))
    print ('Number of last 4 weeks',':',len(oldset))
    print ('Number of this week',':',len(newset))
    
    # Get the new failed case set
    delta = newset - oldset
   # print delta
    print ('Number of new unstable case',':',len(delta))
    
    # Print details info
    dlist = list(delta)

    # Get delta data
    analysis_list(sorted(dlist),newlist)

    # get whole data 
    #olist = list(newset)
    #analysis_list(sorted(olist),oldlist)

def main():
    parser = argparse.ArgumentParser(description='Anasysis unstable cases.')
    parser.add_argument('--model', help='Daily/Weekly report')
    args = parser.parse_args()

    if args.model == 'd':
        daily_report()
    else:
        weekly_report()

if __name__ == "__main__":
    main()
