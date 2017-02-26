from __future__ import print_function

import sys
import urllib
import re

from multiprocessing import Pool
from xml.etree import ElementTree as ET


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

state_xpath='.//*/State'
# cy_rv_xpath='.//*/TotalRevenue'
# state_xpath='.//*/StateAbbreviationCd'
py_rv_xpath=".//*/TotalRevenuePriorYear"
cy_rv_xpath=".//*/TotalRevenueCurrentYear"
business_name_xpath=".//*/BusinessNameLine1"

no_thread=10
filename="data/irs-form-990.txt"


def extract_data(object_id, attempt = 3):
    try :
        url = "https://s32.amazonaws.com/irs-form-990/%s_public.xml" % object_id.strip()
        document = urllib.urlopen(url).read()

        # replace namespace
        document = re.sub(' xmlns="[^"]+"', '', document, count=1)

        page = ET.fromstring(document)

        state = page.find(state_xpath).text

        #current year revenue
        py_rv = page.find(py_rv_xpath).text
        cy_rv = page.find(cy_rv_xpath).text

        name = page.find(business_name_xpath).text

        print( ','.join( (name,state, py_rv, cy_rv ) ) )
    except:
        if attempt > 0 :
            extract_data(object_id, attempt - 1)
        else:
            eprint("%s" % object_id)

def process(filename):
    with open(filename) as f:
        lines = f.readlines()


        lines = lines[1:10]
        # lines = [ '201312259349300236' ]

        p = Pool(no_thread)
        p.map( extract_data, lines)


process(filename)
