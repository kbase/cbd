import argparse
import sys
import os
import traceback
from biokbase.CompressionBasedDistance.Client import _read_inifile, ServerError as CBDServerError
from biokbase.CompressionBasedDistance.Helpers import get_config, parse_input_file
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

      See cbd-buildmatrix for a complete description of all arguments.
'''

desc3 = '''
EXAMPLES
      Build a distance matrix for a set of sequence files where the format is
      determined by the file extension:
      > cbd-buildmatrixlocal mystudy.list

      Build a distance matrix for a set of fastq sequence files:
      > cbd-buildmatrixlocal --format fastq mystudy.list

SEE ALSO
      cbd-buildmatrix
      cbd-getmatrix
      cbd-filtermatrix
      cbd-plotmatrix

AUTHORS
      Mike Mundy 
'''

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='cbd_buildmatrixlocal', epilog=desc3)
    parser.add_argument('inputPath', help='path to file with list of input sequence files', action='store', default=None)
    parser.add_argument('-f', '--format', help='format of input sequence files', action='store', dest='format', default=None)
    parser.add_argument('-s', '--scale', help='scale for distance matrix values', action='store', dest='scale', default='std')
    parser.add_argument('-t', '--trim', help='trim sequence reads to the specified length', action='store', dest='sequenceLen', type=int, default=0)
    parser.add_argument('--min-reads', help='minimum number of reads each sequence file must contain', action='store', dest='minReads', type=int, default=0)
    parser.add_argument('--max-reads', help='maximum number of reads to process from each sequence file', action='store', dest='maxReads', type=int, default=0)
    parser.add_argument('-e', '--show-error', help='show detailed information for an exception', action='store_true', dest='showError', default=False)
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()
    
    # Create input parameters for build_matrix() function.
    input = dict()
    input['scale'] = args.scale
    input['sequence_length'] = args.sequenceLen
    input['min_reads'] = args.minReads
    input['max_reads'] = args.maxReads
    input['node_ids'] = list()
    input['file_paths'] = list()

    # Get an authentication token for the current user.
    auth = _read_inifile()

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

    # For each file, add it to the list.
    for filename in fileList:
        input['file_paths'].append(filename)
        
    # Submit a job to build the distance matrix.
    try:
        worker = CompressionBasedDistance()
        jobid = worker.startJob(get_config(None), auth, input)
    except Exception as e:
        print 'Error starting job: %s' %(e.message)
        if args.showError:
            traceback.print_exc(file=sys.stdout)
        exit(1)

    print "Job '%s' submitted" %(jobid)
    exit(0)
