import argparse
import sys
import os
#from shock import Client as ShockClient
from biokbase.CompressionBasedDistance.Shock import Client as ShockClient
from biokbase.CompressionBasedDistance.Client import CompressionBasedDistance
from biokbase.CompressionBasedDistance.Helpers import get_url

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

      The input-path positional argument is the path to a file with the list of
      paths to the input sequence files.  Each line of of the list file is the
      path to a sequence file.  Each sequence file contains the sequence reads
      for a microbial community.  The --format optional argument specifies the
      type of the sequence files.  Valid formats include 'fasta', 'fastq',
      'clustal', 'embl', 'genbank', 'nexus, and 'seqxml'.

      The output-path positional argument is the path to the output file where
      the distance matrix is stored.  The output file is in csv format with a
      row and column for each sequence file.  The value of each cell in the
      table is the distance between two microbial communities.  A value of 0
      means the two communities are identical and a value of 1 means the two
      communities are completely different.

      The --scale optional argument specifies the scale of the distance values.
      A value of 'std' means to use the standard scale of 0 to 1.  A value of
      'inf' means to use a scale from 0 to infinity.

      The --timeout optional argument specifies the number of seconds to wait
      for a response from the server.  The default is 1800 seconds or 30
      minutes.  A larger timeout might be required if there are many input
      sequence files or the sequence files are large.
'''

desc3 = '''
EXAMPLES
      Build a distance matrix for a set of fasta sequence files:
      > cbd-buildmatrix mystudy.input mystudy.csv

      Build a distance matrix for a set of fastq sequence files:
      > cbd-buildmatrix --format fastq mystudy.input mystudy.csv

AUTHORS
      Mike Mundy, Fang Yang, Nicholas Chia, Patricio Jeraldo 
'''

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='cbd_buildmatrix', epilog=desc3)
    parser.add_argument('inputPath', help='path to file with list of input sequence files', action='store', default=None)
    parser.add_argument('outputPath', help='path to output csv file', action='store', default=None)
    parser.add_argument('-?', '--usage', help='show usage information', action='store_true', dest='usage')
    parser.add_argument('-f', '--format', help='format of input sequence files', action='store', dest='format', default='fasta')
    parser.add_argument('-s', '--scale', help='scale for distance matrix values', action='store', dest='scale', default='std')
    parser.add_argument('-t', '--timeout', help='number of seconds to wait for server response', dest='timeout', default='1800')
    parser.add_argument('--shock-url', help='url for shock service', action='store', dest='shockurl', default='http://kbase.us/services/shock-api/')
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()
    
    if args.usage:
        print usage
        exit(0)

    # Create input parameters for build_matrix() function.
    input = { }
    input['format'] = args.format
    input['scale'] = args.scale
    input['node_ids'] = [ ]

    # Create a cbd client (which must be authenticated).
    cbdClient = CompressionBasedDistance(url=get_url(), timeout=args.timeout)
    
    # Create a shock client.
    shockClient = ShockClient(args.shockurl, cbdClient._headers['AUTHORIZATION'])
    
    # Open the input file with the list of files.
    try:
        infile = open(args.inputPath, "r")
    except IOError as e:
        print "Error opening input list file '%s': %s" %(args.inputPath, e.strerror)
        exit(1)
  
    
    # Open the output file.
    try:
        outfile = open(args.outputPath, 'w')
    except IOError as e:
        print "Error opening output file '%s': %s" %(args.outputPath, e.strerror)
        exit(1)
             
    # Make sure all of the files in the list of files exist. 
    missingFiles = 0
    filelist = []
    for filename in infile:
        filename = filename.strip('\n\r')
        if filename: # Skip empty lines
            if os.path.isfile(filename):
                filelist.append(filename)
            else:
                print "'%s' does not exist" %(filename)
                missingFiles += 1
    infile.close()
    if missingFiles > 0:
        print "%d files do not exist. Update %s with correct file names" %(missingFiles, args.filelist)
        exit(1)
        
    # For each file, upload to shock (keep track of ids).
    for filename in filelist:
        print "Uploading sequence file '%s'" %(filename)
        node = shockClient.create_node(filename, '') # Do I need attributes on the files?
        input['node_ids'].append(node['id'])
        
    # Run the function to build the matrix
    print "Calculating distance matrix"
    output = cbdClient.build_matrix(input)

    # Store the output in the specified file.
    for line in output:
        outfile.write(line)
    outfile.close()
    
    print "Completed"        
    exit(0)