import boto3
from multiprocessing import Pool
from math import ceil
from functools import partial


import json

import time

from multiprocessing import Pool

client = boto3.client('lambda')

no_thread=10
PAUSE_STEP=50
PAUSE_TIME=30 # 1/2min
filename ="data/irs-form-990.txt"

batch=100


def create_record(object_id):
    object_id = object_id.strip()
    return {
        'Data': object_id,
        'ExplicitHashKey': '0',
        'PartitionKey': object_id
    }

def send_data(object_ids, partition_id):

    records = map( create_record, object_ids )
    data = { 'Records': records, 'PartitionKey': partition_id }
    # response = client.put_records(
    #     Records= records,
    #     StreamName='irs900-stream2'
    # )
    response = client.invoke(
        # FunctionName='arn:aws:lambda:eu-west-1:842919366843:function:irs900-manual-invoke',
        FunctionName='irs900-manual-invoke',
        InvocationType='Event',
        LogType='Tail',
        ClientContext='pat-laptop',
        Payload= json.dumps(data),
        Qualifier='$LATEST'
    )

    return response

def process_batch( i, lines, total_batches ) :
    response = send_data( lines[i*batch:(i+1)*batch], i )
    print('batch %d from %d : status %d ' % (i, total_batches, response['ResponseMetadata']['HTTPStatusCode']) )

def process(filename):

    with open(filename) as f:
        lines = f.readlines()


        # todo: read from index file directly
        # lines = lines[1:1000]
        # lines = [ '201312259349300236', '201302269349100970', '201332269349304153' ]

        total_batches = int(ceil(len(lines)*1.0/batch))

        super_steps = int(ceil(total_batches*1.0/PAUSE_STEP))

        partial_process_batch = partial(process_batch, lines = lines, total_batches = total_batches)

        for s in range(super_steps):

            batches = range( s*PAUSE_STEP, min((s+1)*PAUSE_STEP, total_batches) )
            for b in batches:
                partial_process_batch(b)

            time.sleep(PAUSE_TIME)



process(filename)

# response = client.put_records(
#     Records= [ create_record( '201312259349300236') ],
#     StreamName='irs900-stream'
# )
# print(response)
