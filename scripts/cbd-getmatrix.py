import argparse
import sys
import os
import time
import traceback
from biokbase.CompressionBasedDistance.Shock import Client as ShockClient
from biokbase.CompressionBasedDistance.Helpers import job_info_dict
from biokbase.userandjobstate.client import UserAndJobState, ServerError as JobStateServerError

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

      The --show-times optional argument displays the start and finish times
      for successful jobs.

      The --ujs-url optional argument specifies an alternate URL for the user
      and job state service.
'''

desc3 = '''
EXAMPLES
      Get a distance matrix and save to a file:
      > cbd-getmatrix 5285059be4b0ef8357331c34 mystudy.csv

SEE ALSO
      cbd-buildmatrix
      cbd-filtermatrix

AUTHORS
      Mike Mundy 
'''

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='cbd_buildmatrix', epilog=desc3)
    parser.add_argument('jobID', help='path to file with list of input sequence files', action='store', default=None)
    parser.add_argument('outputPath', help='path to output csv file', action='store', default=None)
    parser.add_argument('--show-times', help='show job start and end timestamps', action='store_true', dest='showTimes', default=False)
    parser.add_argument('--ujs-url', help='url for user and job state service', action='store', dest='ujsURL', default='https://kbase.us/services/userandjobstate')
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()
    
    # Get the status of the specified job.
    ujsClient = UserAndJobState(args.ujsURL)
    try:
        info = job_info_dict(ujsClient.get_job_info(args.jobID))
    except JobStateServerError as e:
        print e.message
        exit(1)

    # Check if the job had an error.
    if info['error']:
        print "Job '%s' ended with error '%s' and no results are available." %(args.jobID, info['status'])
        print 'Error details:'
        print ujsClient.get_detailed_error(args.jobID)
        ujsClient.delete_job(args.jobID)
        exit(1)

    # Check if the job is complete.
    if not info['complete']:
        print "Job '%s' has status '%s' and is working on task %s of %s.  Check again later." \
            %(args.jobID, info['status'], info['total_progress'], info['max_progress'])
        exit(1)

    # Show job info.
    if args.showTimes:
        print 'Job started at %s and finished at %s' %(info['started'], info['last_update'])

    # Create a shock client.
    shockClient = ShockClient(info['results']['shockurl'], ujsClient._headers['AUTHORIZATION'])
       
    # Download the output to the specified file and remove the file from shock.
    try:
        shockClient.download_to_path(info['results']['shocknodes'][0], args.outputPath)
    except Exception as e:
        print 'Error downloading distance matrix from %s: %s' %(info['results']['shockurl'], e.message)
        traceback.print_exc(file=sys.stdout)
    try:
        shockClient.delete(info['results']['shocknodes'][0])
    except Exception as e:
        print 'Error deleting distance matrix file from %s: ' %(+info['results']['shockurl'], e.message)
        traceback.print_exc(file=sys.stdout)
    
    # Delete the job.
    ujsClient.delete_job(args.jobID)
    
    exit(0)
