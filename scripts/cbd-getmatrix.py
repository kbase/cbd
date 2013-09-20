import argparse
import sys
import os
import time
import traceback
#from shock import Client as ShockClient
from biokbase.CompressionBasedDistance.Shock import Client as ShockClient
from biokbase.CompressionBasedDistance.Client import CompressionBasedDistance
from biokbase.CompressionBasedDistance.Helpers import get_url
from biokbase.workspaceService.client import workspaceService

desc1 = '''
NAME
      cbd-getmatrix -- get distance matrix from a completed job

SYNOPSIS      
'''

desc2 = '''
DESCRIPTION
      Get a distance matrix from a completed job and save to a file.

      The jobID positional argument is the identifier of the job submitted by
      cbd-buildmatrix to build a distance matrix from a set of sequence files.

      The outputPath positional argument is the path to the output file where
      the distance matrix is stored.  The output file is in csv format with a
      row and column for each input sequence file.  The value of each cell in
      the table is the distance between two microbial communities.  A value of
      0 means the two communities are identical and a value of 1 means the two
      communities are completely different.

      The shock-url and workspace-url optional arguments specify alternate URLs
      for the shock and workspace services.
'''

desc3 = '''
EXAMPLES
      Get a distance matrix and save to a file:
      > cbd-getmatrix job.942 mystudy.csv

SEE ALSO
      cbd-buildmatrix
      kbws-checkjob
      kbws-jobs

AUTHORS
      Mike Mundy 
'''

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='cbd_buildmatrix', epilog=desc3)
    parser.add_argument('jobID', help='path to file with list of input sequence files', action='store', default=None)
    parser.add_argument('outputPath', help='path to output csv file', action='store', default=None)
    parser.add_argument('-?', '--usage', help='show usage information', action='store_true', dest='usage')
    parser.add_argument('--shock-url', help='url for shock service', action='store', dest='shockURL', default='http://kbase.us/services/shock-api/')
    parser.add_argument('--workspace-url', help='url for workspace service', action='store', dest='workspaceURL', default='http://kbase.us/services/workspace/')
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()
    
    if args.usage:
        print usage
        exit(0)

    # Create a cbd client (until workspace supports authenticated clients).
    cbdClient = CompressionBasedDistance(url=get_url())
    
    # Check on the specified job.
    wsClient = workspaceService(args.workspaceURL)
    jobList = wsClient.get_jobs( { 'jobids': [ args.jobID ], 'auth': cbdClient._headers['AUTHORIZATION'] } )
    if len(jobList) == 0:
        print "Job '%s' does not exist!" %(args.jobID)
        exit(1)

    job = jobList[0]
    if job['status'] != 'done':
        print "Job '%s' has status '%s' and is not finished.  Check again later." %(args.jobID, job['status'])
        exit(1)
        
    # Create a shock client.
    shockClient = ShockClient(args.shockURL, cbdClient._headers['AUTHORIZATION'])
       
    # Download the output to the specified file and remove the file from shock.
    shockClient.download_to_path(job['jobdata']['output'], args.outputPath)
    shockClient.delete(job['jobdata']['output'])
    
    # Delete the job.
    wsClient.set_job_status( { 'jobid': job['id'], 'status': 'delete', 'currentStatus': 'done', 'auth': cbdClient._headers['AUTHORIZATION']} )
    
    exit(0)