#! /usr/bin/python

import argparse
import traceback
import sys
from biokbase.workspaceService.client import workspaceService
from biokbase.CompressionBasedDistance.Worker import CompressionBasedDistance

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='RunJob')
    parser.add_argument('jobID', help='identifier of job to run', action='store', default=None)
    parser.add_argument('workspaceURL', help='url of workspace server', action='store', default=None)
    parser.add_argument('token', help='authentication token for user', action='store', default=None)
    args = parser.parse_args()
    
    # Create a workspace client.
    wsClient = workspaceService(args.workspaceURL)
    
    # Get information about the job.
    jobList = wsClient.get_jobs( { 'jobids': [ args.jobID ], 'auth': args.token } )
    if len(jobList) == 0:
        print "Job '%s' does not exist!" %(args.jobID)
        exit(1)
    job = jobList[0]

    # The job must be queued and a cbd type of job.
    if job['status'] != 'queued':
        print "Job '%s' must be in status 'queued' but has status '%s" %(args.jobID, job['status'])
        exit(1)
    if job['type'] != 'cbd':
        print "Job '%s' must be of type 'cbd' but has type '%s'" %(args.jobID, job['type'])
          
    # Create a worker for running the job.
    worker = CompressionBasedDistance()
    
    # Mark job as running and run the job.
    try:
        wsClient.set_job_status( { 'jobid': job['id'], 'status': 'running', 'auth': args.token } )
        output = worker.runJob(job)
        job['jobdata']['output'] = output
        status = 'done'
    except:
        status = 'error'
        traceback.print_exc(file=sys.stderr)
    finally:
        wsClient.set_job_status( { 'jobid': job['id'], 'status': status, 'auth': args.token, 'jobdata': job['jobdata']} )
    
    exit(0)