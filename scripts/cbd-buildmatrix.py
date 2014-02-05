import argparse
import sys
import os
import time
import traceback
#from shock import Client as ShockClient
from biokbase.CompressionBasedDistance.Shock import Client as ShockClient
from biokbase.CompressionBasedDistance.Client import CompressionBasedDistance
from biokbase.CompressionBasedDistance.Helpers import get_url, parse_input_file

desc1 = '''
NAME
      cbd-buildmatrix -- build a distance matrix to compare microbiota samples

SYNOPSIS      
'''

desc2 = '''
DESCRIPTION
      Build a distance matrix from a set of sequence files for microbiota
      comparisons.  Compression based distance uses the relative compression
      of combined and individual datasets to quantify overlaps between
      microbial communities.

      The inputPath positional argument is the path to a file with the list of
      paths to the input sequence files and the groups each file belongs to.
      Each line of the list file has two tab delimited fields: (1) path to a
      sequence file, (2) list of groups the sequence file belongs to.  Each
      sequence file contains the sequence reads for a microbial community.  The
      list of groups is a semicolon delimited list of group names.  In the
      following example, the sample1 fasta sequence file includes groups
      subject1 and day7.

          /myhome/sample1.fasta    subject1;day7

      Note that the group list field is not used by cbd-buildmatrix.

      The --format optional argument specifies the type of the sequence files.
      Valid formats include 'fasta', 'fastq', 'clustal', 'embl', 'genbank',
      'nexus, and 'seqxml'.  All of the sequence files must be in the same
      format.  If the --format argument is not specified, the format is set
      from the extension of the sequence files.

      The --scale optional argument specifies the scale of the distance values.
      A value of 'std' means to use the standard scale of 0 to 1, where 0 means
      the two communities are identical and a value of 1 means the two
      communities are completely different.  A value of 'inf' means to use a
      scale from 0 to infinity.

      A job is started to build the distance matrix and the job id is returned.
      Use the cbd-getmatrix command to monitor the status of the job.  When the
      job is done, the cbd-getmatrix command saves the distance matrix to a
      file.
'''

desc3 = '''
EXAMPLES
      Build a distance matrix for a set of sequence files where the format is
      determined by the file extension:
      > cbd-buildmatrix mystudy.list

      Build a distance matrix for a set of fastq sequence files:
      > cbd-buildmatrix --format fastq mystudy.list

SEE ALSO
      cbd-getmatrix
      cbd-filtermatrix
      cbd-plotmatrix

AUTHORS
      Mike Mundy, Fang Yang, Nicholas Chia, Patricio Jeraldo 
'''

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='cbd_buildmatrix', epilog=desc3)
    parser.add_argument('inputPath', help='path to file with list of input sequence files', action='store', default=None)
    parser.add_argument('-f', '--format', help='format of input sequence files', action='store', dest='format', default=None)
    parser.add_argument('-s', '--scale', help='scale for distance matrix values', action='store', dest='scale', default='std')
#    parser.add_argument('-u', '--url', help='url for cbd service', action='store', dest='url', default='http://kbase.us/services/cbd/')
    parser.add_argument('--shock-url', help='url for shock service', action='store', dest='shockurl', default='http://kbase.us/services/shock-api/')
    parser.add_argument('-e', '--show-error', help='show detailed information for an exception', action='store_true', dest='showError', default=False)
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()
    
    # Create input parameters for build_matrix() function.
    input = dict()
    input['scale'] = args.scale
    input['node_ids'] = list()

    # Create a cbd client (which must be authenticated).
    cbdClient = CompressionBasedDistance(url=get_url())
    
    # Create a shock client.
    shockClient = ShockClient(args.shockurl, cbdClient._headers['AUTHORIZATION'])
    
    # Parse the input file with the list of sequence files.
    (fileList, extensions, numMissingFiles) = parse_input_file(args.inputPath)
    if numMissingFiles > 0:
        exit(1)

    # Set the format based on the sequence file extension if the format argument was not specified.
    if args.format is None:
        if len(extensions) == 1:
            input['format'] = extensions.keys()[0]
        else:
            print "The format of the sequence files could not be determined.  Set the format with the --format argument."
            exit(1)
    else:
        input['format'] = args.format
        
    # For each file, upload to shock (keep track of ids).
    for filename in fileList:
        print "Uploading sequence file '%s'" %(filename)
        node = shockClient.create_node(filename, '')
        input['node_ids'].append(node['id'])
        
    # Submit a job to build the distance matrix.
    try:
        jobid = cbdClient.build_matrix(input)
    except Exception as e:
        print 'Error starting job: %s' %(e.message)
        if args.showError:
            traceback.print_exc(file=sys.stdout)
        # Delete all of the input files from shock if something went wrong.
        for nodeId in input['node_ids']:
            shockClient.delete(nodeId)
        exit(1)

    print "Job '%s' submitted" %(jobid)
    exit(0)
