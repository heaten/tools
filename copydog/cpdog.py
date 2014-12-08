#!/usr/bin/env python2.7
import sys
import os
import subprocess
import argparse

class IspLog(object):
    def __init__(self,object):
	self.path = object
	self.failed_case = self.parse_isp_log()
    def parse_isp_log(self):
	list = []
	f = open(self.path,'r')
	##print'name is',f.name
	fdata = f.readlines()
	for line in fdata:
	    ##print line
            if 'ts_' in line: 
                seg = line.split(';')
                (_suite, case) = seg[3].split(':')
		list.append(case)
	f.close()
	return list
    def get_last_case(self):
	##print self.failed_case
	failed_case =  self.failed_case[len(self.failed_case)-1]
	case_num =fetch_case_num (failed_case)
	return case_num

def fetch_case_num(case):
    case_f = case.split('_',3)
    print case_f
    case_num = case_f[0]+'_'+case_f[1]+'_'+case_f[2]
    return case_num

def main():
    defaultname = 'erlang'
    parser = argparse.ArgumentParser(description='Automatic copy log to my home')
    parser.add_argument('-n', '--name', help='Name the log file by yourself',default = defaultname, dest='n')
    args = parser.parse_args()
    loglist = IspLog('/tmp/DPE_COMMONLOG/isp.log')
    case_num =  loglist.get_last_case()
    if args.n == defaultname:
	log_name = case_num
    else:
	log_name = defaultname
    subprocess.call('cp /tmp/DPE_COMMONLOG/Erlang_trace_merged.log ~/'+log_name+'.log',shell =True)


if __name__ == "__main__":
    main()
