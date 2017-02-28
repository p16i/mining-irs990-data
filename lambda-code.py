from __future__ import print_function

import boto3
import json
import urllib
import re

from xml.etree import ElementTree as ET

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

state_xpath         ='.//*/State'
py_rv_xpath         =".//*/TotalRevenuePriorYear"
cy_rv_xpath         =".//*/TotalRevenueCurrentYear"
business_name_xpath =".//*/BusinessNameLine1"
irs900_xpath        = ".//*/IRS990"


def lambda_handler(event, context):
    s3 = boto3.resource('s3')

    success_basket = []
    failed_basket  = []

    for record in event['Records'] :
        object_id=record["Data"]
        irs900_form = extract_data(object_id)
        if irs900_form is not None:
            success_basket.append( ",".join(irs900_form) )
            print(irs900_form)
        else :
            failed_basket.append(object_id)

    partition = 'success/partition-%s.txt' % event['PartitionKey']
    s3.Bucket('irs900-collection').put_object(Key=partition, Body= '\n'.join(success_basket) )

    if len(failed_basket) > 0 :
        failed_partition = 'failed/partition-%s.txt' % event['PartitionKey']
        s3.Bucket('irs900-collection').put_object(Key=failed_partition, Body= '\n'.join(failed_basket) )

    return respond(None, "ok")

def extract_data(object_id, attempt = 3):
    object_id = object_id.strip()
    try :
        url = "https://s3.amazonaws.com/irs-form-990/%s_public.xml" % object_id
        document = urllib.urlopen(url).read()

        # replace namespace
        document = re.sub(' xmlns="[^"]+"', '', document, count=1)

        page = ET.fromstring(document)

        state = page.find(state_xpath).text

        py_rv = "0"
        py_rv_node = page.find(py_rv_xpath)
        if py_rv_node is not None:
            py_rv = py_rv_node.text

        cy_rv = "0"
        cy_rv_node = page.find(cy_rv_xpath)
        if cy_rv_node is not None:
            cy_rv = cy_rv_node.text

        name = page.find(business_name_xpath).text

        return (object_id, name, state, py_rv, cy_rv)

    except Exception as e:
        if attempt > 0 :
            extract_data(object_id, attempt - 1)
        else:
            return
