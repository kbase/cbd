#! /usr/bin/python

import argparse
import traceback
import sys
import json
from biokbase.CompressionBasedDistance.Worker import CompressionBasedDistance
from biokbase.userandjobstate.client import UserAndJobState

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='cbd-runjob')
    parser.add_argument('jobDataPath', help='path to job data file', action='store', default=None)
    args = parser.parse_args()
    
    # Run the job.
    job = json.load(open(args.jobDataPath, 'r'))
    try:
        worker = CompressionBasedDistance()
        worker.runJob(job)
    except Exception as e:
        # Mark the job as failed.
        tb = traceback.format_exc()
        sys.stderr.write(tb)
        ujsClient = UserAndJobState(job['config']['userandjobstate_url'], token=job['context']['token'])
        ujsClient.complete_job(job['id'], job['context']['token'], 'failed', tb, { })
    
    exit(0)
