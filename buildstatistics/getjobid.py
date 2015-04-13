import datetime
import getpass
import glob
import os
import re
import sys
import threading
import time

sys.path.append('/proj/cims_sgsn/prod/portal/lib/site-packages')
os.environ['CIMS_CONFIG_PATH'] = '/proj/grit/portal/conf'
import pycims.cimsapi as cims
testqueue_api = cims.CimsApi('testqueue')
event_api = cims.CimsApi('event')
build_api = cims.CimsApi('build')

# PORTAL STUFF
def downloadResults(startday,endday,branchname = 'ndpgsn_5_0_lsv_001'):
    result = []
    job_types = ['test_gttonnextgen']
    for job_type in job_types:
        job_ids = testqueue_api.getListOfJobIds(product = branchname,
                                                job_type = job_type,
                                                start = startday,
                                                end = endday,
                                                filters = {})['data']
    return job_ids 

if __name__=="__main__":
    print 'Hello'
    ids = downloadResults()
    print ids
