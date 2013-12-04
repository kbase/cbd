import argparse
import sys
import os
import time
import traceback
from biokbase.CompressionBasedDistance.Client import _read_inifile
from biokbase.CompressionBasedDistance.Helpers import get_config
from biokbase.CompressionBasedDistance.Worker import CompressionBasedDistance

desc1 = '''
NAME
      cbd-buildmatrixlocal -- build a distance matrix to compare microbiota samples
                              on local system

SYNOPSIS      
'''

desc2 = '''
DESCRIPTION
      Build a distance matrix from a set of sequence files for microbiota
      comparisons.  Compression based distance uses the relative compression
      of combined and individual datasets to quantify overlaps between
      microbial communities.  The job started to build the distance matrix is
      run on the local system.

      The inputPath positional argument is the path to a file with the list of
      paths to the input sequence files and the groups each file belongs to.
      Each line of the list file has two tab delimited fields: (1) path to a
      sequence file, (2) list of groups the sequence file belongs to.  Each
      sequence file contains the sequence reads for a microbial community.  The
      list of groups is a semicolon delimited list of group names.  In the
      following example, the sample1 fasta sequence file includes groups
      patient1 and day7.

          /myhome/sample1.fasta    patient1;day7

      Note that the group list field is not used by cbd-buildmatrix.

      The --format optional argument specifies the type of the sequence files.
      Valid formats include 'fasta', 'fastq', 'clustal', 'embl', 'genbank',
     'nexus, and 'seqxml'.

      The --scale optional argument specifies the scale of the distance values.
      A value of 'std' means to use the standard scale of 0 to 1.  A value of
      'inf' means to use a scale from 0 to infinity.

      A job is started to build the distance matrix and the job id is returned.
      Use the cbd-getmatrix command to monitor the status of the job.  When the
      job is done, the cbd-getmatrix command saves the distance matrix to a
      file.
'''

desc3 = '''
EXAMPLES
      Build a distance matrix for a set of fasta sequence files:
      > cbd-buildmatrix mystudy.input

      Build a distance matrix for a set of fastq sequence files:
      > cbd-buildmatrix --format fastq mystudy.input

SEE ALSO
      cbd-buildmatrix
      cbd-getmatrix
      cbd-filtermatrix

AUTHORS
      Mike Mundy, Fang Yang, Nicholas Chia, Patricio Jeraldo 
'''

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='cbd_buildmatrix', epilog=desc3)
    parser.add_argument('inputPath', help='path to file with list of input sequence files', action='store', default=None)
    parser.add_argument('-f', '--format', help='format of input sequence files', action='store', dest='format', default='fasta')
    parser.add_argument('-s', '--scale', help='scale for distance matrix values', action='store', dest='scale', default='std')
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()
    
    # Create input parameters for build_matrix() function.
    input = dict()
    input['format'] = args.format
    input['scale'] = args.scale
    input['node_ids'] = list()
    input['file_paths'] = list()

    # Create a cbd client (which must be authenticated).
    auth = _read_inifile()
    
    # Open the input file with the list of files.
    try:
        infile = open(args.inputPath, "r")
    except IOError as e:
        print "Error opening input list file '%s': %s" %(args.inputPath, e.strerror)
        exit(1)
  
    # Make sure all of the files in the list of files exist. 
    missingFiles = 0
    filelist = []
    for line in infile:
        line = line.strip('\n\r')
        if line and line[0] != '#': # Skip empty lines
            fields = line.split('\t')
            filename = fields[0]
            if os.path.isfile(filename):
                filelist.append(filename)
            else:
                print "'%s' does not exist" %(filename)
                missingFiles += 1
    infile.close()
    if missingFiles > 0:
        print "%d files are not accessible. Update %s with correct file names" %(missingFiles, args.inputPath)
        exit(1)
        
    # For each file, upload to shock (keep track of ids).
    for filename in filelist:
        input['file_paths'].append(filename)
        
    # Submit a job to build the distance matrix.
    try:
        worker = CompressionBasedDistance()
        jobid = worker.startJob(get_config(None), auth, input)
    except:
        traceback.print_exc(file=sys.stderr)
        exit(1)

    print "Job '%s' submitted" %(jobid)
    exit(0)
