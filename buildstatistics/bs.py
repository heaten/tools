#! /usr/bin/env python2.7
import os
import sys
import logging
import argparse

from lxml import etree
from Levenshtein import ratio
from collections import defaultdict
from getjobid import downloadResults

os.environ['CIMS_CONFIG_PATH'] = '/proj/tecsomaten/etc'
sys.path.append('/proj/tecsomaten/lib')
import pycims.cimsapi

idlist = [77697,77890,77978,78049,78198,78199,78466,78500,78671,78762,78837,79495,\
79529,79636,79761,79785,79880,79927,79954,80001,80052,80096,80195,80230,80279,80584,80601,80637,80721,\
80785,80858,80894,80900,80918,80943,80958,81000,81064,81085,81128,81209,81254,81366,81384,81399,81438,\
81471,81576,81827,82114,82234,82328,82384,82437,82508,82567,82571,82614,82721,82900,82906,82986,83199,\
83285,83314,83324,83449,83543,83571,83650,83702,83741,83814,83887,84008,84013,84355,84422]

idlisttest = [83285,83314]
idlist10 = [83285,83314,83324,83449,83543,\
              83571,83650,83702,83741,83814,\
              83887,84008,84013,84355,84422]
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

def get_fail_result(ids):
    results = []
    for id in ids:
	print 'Now start to get fail case,id is = %s'%id
	result = RegressionResult(id)
	results.extend(result.failed_tcs)
    return results

def parse_job_id():
	f = open('joblist.log','r')
	joblist = f.readlines()
	for j in joblist:
		print j, 
	return joblist

def insert(name,miss_list):
	if name not in miss_list:
		miss_list.append(name)
	return miss_list
def add_config(obj):
    return obj.name+'.'+obj.config

def main():
    idport = downloadResults()
    print idport
    base = RegressionResult(idport[0])
    latest = RegressionResult(idport[-1])
    base_case = base.get_all_cases()
    latest_case = latest.get_all_cases()
    # Read job list from file
    # ids = parse_job_id() 
    #fail_record = get_fail_result(idlist)
    tmp_fail_record = get_fail_result(idport)
    fail_record = map(add_config, tmp_fail_record)
    coast = 0
    miss_list = []
    all_miss_list = []
    for f in fail_record:
        if f in base_case.keys():
            coast = coast+1
        else:
            insert(f, miss_list)
            all_miss_list.append(f)
            continue
    for m in miss_list:
        print '*'*100
	print m
	print all_miss_list.count(m)

    print '*'*100    
    print 'legacy_record  is = %s'%coast
    length = len(fail_record)
    lengthb = len(base_case.keys())
    lengthl = len(latest_case.keys())
    lengthm = len(miss_list)
    print 'fail_record    is = %s'%length
    print 'base lenght    is = %s'%lengthb
    print 'latest lenghl  is = %s'%lengthl
    print 'miss  lenghl   is = %s'%lengthm
    print miss_list
    
    return coast 

if __name__ == "__main__":
	main()



