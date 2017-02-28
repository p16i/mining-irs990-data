import boto3
import json
import time
import sys

from math import ceil
from functools import partial

PAUSE_STEP=50
PAUSE_TIME=30 # 1/2min
BATCH_SIZE=100

lamda_client = boto3.client('lambda')


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
    response = lamda_client.invoke(
        FunctionName='irs900-manual-invoke',
        InvocationType='Event',
        LogType='Tail',
        ClientContext='pat-laptop',
        Payload= json.dumps(data),
        Qualifier='$LATEST'
    )

    return response

def process_batch( i, document_ids, total_batches ) :
    start_idx = i*BATCH_SIZE
    end_idx   = (i+1)*BATCH_SIZE
    response = send_data( document_ids[start_idx:end_idx], i )
    print('batch %d from %d : status %d ' % (i, total_batches, response['ResponseMetadata']['HTTPStatusCode']) )

def is_revelant_form( line ):
    data = line.split(',')

    if data[6] in ['990', '990O']:
        return True
    return False

def process(filename):

    with open(filename) as f:
        lines = f.readlines()

        # for debug proposes
        # lines = lines[1:20000]

        revelant_forms = filter( is_revelant_form, lines[1:] )
        document_ids   = map( lambda f: f.split(',')[-1].strip(), revelant_forms )

        total_batches = int(ceil(len(document_ids)*1.0/BATCH_SIZE))
        super_steps   = int(ceil(total_batches*1.0/PAUSE_STEP))

        print("We have %s batches and %d super_steps"
              % ( total_batches, super_steps )
        )

        partial_process_batch = partial(process_batch, document_ids = document_ids, total_batches = total_batches)

        for s in range(super_steps):

            batches = range( s*PAUSE_STEP, min((s+1)*PAUSE_STEP, total_batches) )
            for b in batches:
                partial_process_batch(b)

            # prevent exceeding no. concurrent lamda tasks ( limited 100 concurrent tasks)
            print('Pause for %d' % PAUSE_TIME)
            time.sleep(PAUSE_TIME)



filename = sys.argv[1]

print( 'Processing %s ' % filename )
process(filename)
