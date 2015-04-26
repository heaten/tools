#! /usr/bin/env python2.7
import os
import sys
import logging
import argparse
import pickle
import time
import datetime

from lxml import etree
from Levenshtein import ratio
from collections import defaultdict
from getjobid import downloadResults

os.environ['CIMS_CONFIG_PATH'] = '/proj/tecsomaten/etc'
sys.path.append('/proj/tecsomaten/lib')
import pycims.cimsapi

class RegressionResult(object):
    def __init__(self, reg_id):
        self.failed_tcs = []
        self.test_cases = dict()
        self.reg_id = reg_id
        self.get_results()
    
    def get_failed_tests_with_tr(self):
        sgsn_api = pycims.cimsapi.CimsApi('sgsnexternal')
        testcases = sgsn_api.getFailedCasesByJobId(jobId=self.reg_id, withTR=True)
        return testcases.get('data')

    def get_results(self):
        #logging.debug('collecting results for %s', self.reg_id)
        cimsif = CimsInterface()
        try:
			data = cimsif.get_job_tree(self.reg_id)
        except Exception, e:
            logging.error('getting results failed: %s', str(e))
            sys.exit(str(e))
        configs = data['tree'][0]['children'] 
        for c in configs:
            logging.debug('found configuration: %s', c['name'])
            suites = c['children']
            for ts in suites:
                try:
                    for tc in ts['children']:
                        tc_obj = TestCaseResult(tc, ts['name'], self.reg_id, c['name'])
                        tc_n = tc_obj.name+'.'+tc_obj.config
                        self.test_cases[tc_n] = tc_obj
                        if not tc_obj.passed:
                            self.failed_tcs.append(tc_obj)
                except KeyError:
                    # The test suite didn't have any children
                    # i.e. the suite contained no tests that 
                    # were executed
                    logging.debug('no tests in suite')
                    continue

    def get_all_cases(self):
        return self.test_cases
    def get_fail_percentage(self):
        return (1 - (float(len(self.failed_tcs)) / float(len(self.test_cases)))) * 100

    def get_failed_tests(self):
        return self.failed_tcs

    def to_xml(self):
        root = etree.Element('regression', {'id':self.reg_id})
        for t in self.failed_tcs:
            root.append(t.to_xml())
        fn = "%s.xml" % self.reg_id
        out_file = open(fn, 'w')
        out_file.write(etree.tostring(root, pretty_print=True))

class CimsInterface(object):
    def get_job_tree(self, job_id):
        chunk_size = 200
        event_api = pycims.cimsapi.CimsApi('event')
        jobtree = event_api.getJobTreeById(
                {'id': job_id,
                 'includeInfos': True,
                 'includeMeasurements': False,
                 'nonLeavesOnly': True})['data']

        nonleaf_ids = list(self._get_all_ids(jobtree['tree']))

        leafs = []
        chunks = [nonleaf_ids[i:i + chunk_size] for i in range(0, len(nonleaf_ids), chunk_size)]

        for ids in chunks:
            data = event_api.getJobEventChildren(
                    {'parentIds': ids,
                     'includeInfos': True,
                     'includeMeasurements': False})['data']
            leafs.extend(data)
        
        self._rebuild_job_tree(jobtree['tree'], leafs)
        return jobtree

    def _rebuild_job_tree(self, tree, leafs):
        def _rebuild(tree, children_by_parent):
            for node in tree:
                if node['id'] in children_by_parent:
                    if 'children' not in node:
                        node['children'] = []
                    child_ids = set(child['id'] for child in node['children'])
                    new_children = [c for c in children_by_parent[node['id']] 
                                    if c['id'] not in child_ids]
                    node['children'] += new_children
                if 'children' in node:
                    _rebuild(node['children'], children_by_parent)
    
        children_by_parent = defaultdict(lambda: [])
        for leaf in leafs:
            parent = leaf['parent']
            del leaf['parent']
            children_by_parent[parent].append(leaf)

        _rebuild(tree, children_by_parent)

    
    def _get_all_ids(self, tree):
        ids = set()
        for node in tree:
            if 'id' in node:
                ids.add(node['id'])
            if 'children' in node:
                ids = ids.union(self._get_all_ids(node['children']))
        return ids

class TestCaseResult(object):
    def __init__(self, tc, suite, reg_id, config):
        self.name = tc['name']
        self.passed = tc['verdict'] == "PASS"
        self.suite = suite
        self.reg_id = reg_id
        self.config = config
        if not self.passed:
            for info in tc['eventinfos']:
                if "FAIL@" in info['attribute']:
                    tokens = info['value'].split(',', 3)
                    self.fail_reason = self._replace_common(tokens[3])
                elif "ERROR@" in info['attribute']:
                    self.fail_reason = info['value']

    def _replace_common(self, input_string):
        return input_string.replace(self.suite, "").replace("/vobs/gsn/product/test/gtt/core/components", "").replace("/vobs/gsn/product/test/gtt/product/", "").replace(self.name, "")

    def to_xml(self):
        xml_rep = etree.Element('tc', {'name':self.name, 'passed':'%s' % self.passed})
        reason = etree.Element('reason')
        reason.text = self.fail_reason
        xml_rep.append(reason)
        return xml_rep

class BuildResult(object):
    def __init__(self,id,number):
        self.id = id
        self.number = number

def get_fail_result(ids):
    results = []
    for id in ids:
	print 'Now start to get fail case,id is = %s'%id
	result = RegressionResult(id)
	results.extend(result.failed_tcs)

    return results


def get_fail_number(ids):
    print ids
    flist = []
    for id in ids:
        namelist = []
        print 'Now start to get fail number, id is %s'%id
        result = RegressionResult(id)     
        for i in result.failed_tcs:
            namelist.append(i.name)
        
        #remove the caes wit same config
        nset = set(namelist)
        rlist = list(nset)
        
        #Summrize reuslt for each build
        build = BuildResult(id,len(rlist))

        # List result
        flist.append(build)
        print build.id
        print build.number
    return flist


def insert(name,miss_list):
	if name not in miss_list:
		miss_list.append(name)
	return miss_list

def add_config(obj):
    return obj.name+'.'+obj.config

def write_all_results(id_list):
    weekn = 1
    for i in id_list:
        tmp_fail_record = get_fail_result(i)
        fail_record = map(add_config, tmp_fail_record)
        filename ='w'+'%s'%weekn+'.txt' 
        ft = open(filename,'w')
        pickle.dump(fail_record,ft)
        ft.close()
        weekn= weekn+1

def main():
    w1 = downloadResults('2014-11-03 00:00:00','2014-11-09 24:00:00') 
    w2 = downloadResults('2014-11-10 00:00:00','2014-11-16 24:00:00')
    w3 = downloadResults('2014-11-17 00:00:00','2014-11-23 24:00:00')
    w4 = downloadResults('2014-11-24 00:00:00','2014-11-30 24:00:00')
    
    w5 = downloadResults('2014-12-01 00:00:00','2014-12-07 24:00:00')
    w6 = downloadResults('2014-12-08 00:00:00','2014-12-14 24:00:00')
    w7 = downloadResults('2014-12-15 00:00:00','2014-12-21 24:00:00')
    w8 = downloadResults('2014-12-22 00:00:00','2014-12-28 24:00:00')
    w9 = downloadResults('2014-12-29 00:00:00','2015-01-04 24:00:00')
    
    w10 = downloadResults('2015-01-05 00:00:00','2015-01-11 24:00:00') 
    w11 = downloadResults('2015-01-12 00:00:00','2015-01-18 24:00:00')
    w12 = downloadResults('2015-01-19 00:00:00','2015-01-25 24:00:00')
    w13 = downloadResults('2015-01-26 00:00:00','2015-02-01 24:00:00')
    
    w14 = downloadResults('2015-02-02 00:00:00','2015-02-08 24:00:00')
    w15 = downloadResults('2015-02-09 00:00:00','2015-02-15 24:00:00') 
    w16 = downloadResults('2015-02-16 00:00:00','2015-02-22 24:00:00')
    w17 = downloadResults('2015-02-23 00:00:00','2015-03-01 24:00:00')
    
    w18 = downloadResults('2015-03-02 00:00:00','2015-03-08 24:00:00')
    w19 = downloadResults('2015-03-09 00:00:00','2015-03-15 24:00:00')
    w20 = downloadResults('2015-03-16 00:00:00','2015-03-22 24:00:00')
    w21 = downloadResults('2015-03-23 00:00:00','2015-03-29 24:00:00') #bad boy
    
    w22 = downloadResults('2015-03-30 00:00:00','2015-04-05 24:00:00')
    w23 = downloadResults('2015-04-06 00:00:00','2015-04-12 24:00:00')
    w24 = downloadResults('2015-04-13 00:00:00','2015-04-19 24:00:00')
    w25 = downloadResults('2015-04-20 00:00:00','2015-04-26 24:00:00')
    w26 = downloadResults('2015-04-27 00:00:00','2015-05-03 24:00:00')

    
    id_list = [w1,w2,w3,w4,w5,w6,w7,w8,w9,w10,w11,w12,w13,w14,w15,w16,w17,w18,w19,w20,w21,w22,w23,w24,w25]
   
    print id_list[-1]

    #write_all_results(id_list)
    #write_delta_results(25,w25)
    write_daily_data()


def write_delta_results(weekn,week):    
    tmp_fail_record = get_fail_result(week)
    fail_record = map(add_config, tmp_fail_record)
    filename ='w'+'%s'%weekn+'.txt' 
    ft = open(filename,'w')
    pickle.dump(fail_record,ft)
    ft.close()

def write_daily_data():
    # get job id for yesterday
    timeslot = get_timeslot()
    jobidlist = downloadResults(timeslot[0],timeslot[1])
    buildresult = get_fail_number(jobidlist)

    #Read old data
    filename = 'FailNumber.txt'
    ft = open(filename,'r')
    data = pickle.load(ft)
    ft.close()

    #Add new data
    ft = open(filename,'w')
    new = data+buildresult
    pickle.dump(new,ft)
    ft.close()

def get_timeslot():
    #today = time.strftime("%Y-%m-%d %X",time.localtime())
    today = datetime.datetime.now()
    y = today - datetime.timedelta(days=1)
    
    yesterday = time.strftime("%Y-%m-%d %X",y.timetuple())

    begin = yesterday[:11]+'00:00:00'
    end = yesterday[:11]+'24:00:00'
    print begin
    print end
    return [begin,end]

if __name__ == "__main__":
	main()



