#!/proj/sgsn-tools/wh/bin/sgenv python
import os
import sys
import pickle
import argparse
import collections
from fetchdata import fetch_data

#Globe
x = 1
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
    # Initial data 
    sum = 0 
    print 'Start to use class counter'
    c = collections.Counter()
    
    # Update counter class with raw_l
    c.update(raw_l)
  
    # Counter new unstable case
    for d in delta_l:
        time = c[d]
        if time >x:
            print '%-130s:%5d'%(d,time)
            sum= sum+1
    print 'The number of new unstable case is %s'%sum 
    
    # Method of most_common
    top15 = c.most_common(15)
    print '='*115
    for t in top15:
        print '%-130s:%5d'%(t[0],t[1])
   

def daily_report_private():
    filename = 'FailNumber.txt'    
    ft = open(path+filename,'r')
    data = pickle.load(ft)
    ft.close()
    list =[]
    ignore = 0
    for d in data:
        if d.id == '114272':
            ignore = ignore +1
        elif d.id == '114212':
            ignore = ignore +1          
        else:
            list.append(d.number)
    # print 'The whole record is: %s'%list
    list10 = list[-10:]
    #print 'The latest 10 record is: %s'%list10
    list10.sort(key = int)
    print 'The sorted 10 record is: %s'%list10

def daily_report():
    list2 = fetch_data()
    list10 = list2[-10:]
    list10.sort(key=int)
    print 'The sorted 10 record is: %s'%list10

def weekly_report():
    # Read the legacy record
    oldlist = read_data([29,30,31,32])
    # Read the latest record
    newlist = read_data([33])
    
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
    nlist = list(newset)

    # Get delta data
    analysis_list(sorted(dlist),newlist)

def delta_report():
    filename = 'newcase301_525.txt'
    ft = open(path + filename,'r')
    data = pickle.load(ft)
    ft.close()
    print len(data)
    whole = read_data([17,18,19,20,22,23,24,25,26,27,28])
    analysis_list(sorted(data),whole)

def main():
    parser = argparse.ArgumentParser(description='Anasysis unstable cases.')
    parser.add_argument('--model', help='Daily/Weekly report')
    args = parser.parse_args()

    if args.model == 'd':
        daily_report()
    elif args.model == 'c':
        delta_report()
    else:
        weekly_report()

if __name__ == "__main__":
    main()
