import argparse
import sys
import os
import numpy

desc1 = '''
NAME
      cbd-filtermatrix -- apply a filter to a distance matrix

SYNOPSIS      
'''

desc2 = '''
DESCRIPTION
      Apply a filter to a distance matrix to select groups for microbiota
      comparisons.

      The inputPath positional argument is the path to a file with the list of
      paths to the input sequence files and the groups each file belongs to.
      Each line of the list file has two tab delimited fields: (1) path to a
      sequence file, (2) list of groups the sequence file belongs to.  Each
      sequence file contains the sequence reads for a microbial community.  The
      list of groups is a semicolon delimited list of group names.  In the
      following example, the sample1 fasta sequence file includes groups
      subject1 and day7.

          /myhome/sample1.fasta    subject1;day7

      The sourcePath positional argument is the path to the source distance
      matrix created by cbd-buildmatrix and saved by cbd-getmatrix.

      The destPath positional argument is the path to the destination distance
      matrix after the filter is applied.

      The group positional argument is the list of groups to apply with the
      filter.  The list is a semicolon delimited list of group names.

      The --filter optional argument specifies the filter to apply to the source
      distance matrix.  Valid filters are 'within' to select one group,
     'without' to exclude one group, and 'between' to select multiple groups.
'''

desc3 = '''
EXAMPLES
      Filter a distance matrix to select samples within group subject1:
      > cbd-filtermatrix mystudy.input mystudy.csv dest.csv subject1

      Filter a distance matrix exclude samples with group subject5:
      > cbd-filtermatrix --filter without
        mystudy.input mystudy.csv dest.csv subject5

      Filter a distance matrix to select samples between groups day0, day7,
      and day14:
      > cbd-filtermatrix --filter between 
        mystudy.input mystudy.csv dest.csv 'day0;day7;day14'

SEE ALSO
      cbd-buildmatrix
      cbd-getmatrix

AUTHORS
      Mike Mundy 
'''

# Special value to indicate entry is not included.
NA = -1.0

''' Check if the specified ID is in the list of selected groups. '''

def isIdSelected(id, groupToId, groupList):
    for group in groupList:
        if id in groupToId[group]:
            return True
    return False

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='cbd-filtermatrix', epilog=desc3)
    parser.add_argument('inputPath', help='path to file with list of input sequence files', action='store', default=None)
    parser.add_argument('sourcePath', help='path to source distance matrix file', action='store', default=None)
    parser.add_argument('destPath', help='path to destination distance matrix file', action='store', default=None)
    parser.add_argument('group', help='list of group identifiers (separated by semicolon)', action='store', default=None)
    parser.add_argument('-f', '--filter', help='type of filter (within, without, or between)', action='store', dest='filter', default='within')
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()
    
    # Parse the list of group identifiers.
    groupList = args.group.split(';')
    
    # Open the input file with the list of files.
    try:
        infile = open(args.inputPath, 'r')
    except IOError as e:
        print "Error opening input list file '%s': %s" %(args.inputPath, e.strerror)
        exit(1)
  
    # Parse the input file and assign IDs to groups. 
    groupToId = dict()
    for line in infile:
        line = line.strip('\n\r')
        if line and line[0] != '#': # Skip empty and comment lines
            fields = line.split('\t')
            if len(fields) < 2 or len(fields) > 3:
                print "Each line must contain a path and group list and an optional label.  The following line contains %d fields:" %(len(fields))
                print "  " + line
                exit(1)
            filePath = fields[0]
            groups = fields[1].split(';')
            
            # Add an entry to the dictionary for the ID.
            fileName = os.path.basename(filePath)
            sampleID = os.path.splitext(fileName)[0]
            for group in groups:
                if group not in groupToId.keys():
                    groupToId[group] = list()
                groupToId[group].append(sampleID)
    infile.close()
    
    # Open the source distance matrix file.
    try:
        sourceFile = open(args.sourcePath, 'r')
    except IOError as e:
        print "Error opening source distance matrix file '%s': %s" %(args.sourcePath, e.strerror)
        exit(1)
  
    # Get the list of IDs from the first line of the source file.
    line = sourceFile.readline()
    line = line.strip('\n\r')
    idList = line.split(',')
    idList.pop(0) # Remove the first entry which is always 'ID'
    
    # Read the source distance matrix from the source file. 
    sourceArray = numpy.zeros((len(idList),len(idList)), dtype=float)
    row = 0
    for line in sourceFile:
        line = line.strip('\n\r')
        fields = line.split(',')
        fields.pop(0) # Remove the first field which is the ID
        for index in range(0,len(fields)):
            sourceArray[row,index] = fields[index]
        row += 1
    sourceFile.close()
        
    # Create the destination array and initialize to special value.
    destArray = numpy.empty((len(idList),len(idList)), dtype=float)
    destArray.fill(NA)

    # For filters 'within' and 'between', find all of the values in the specified group.
    if args.filter == 'within' or args.filter == 'between':
        if args.filter == 'within'  and len(groupList) != 1:
            print "Only one group can be specified with filter 'within'"
            exit(1)
        for row in range(0,len(idList)):
            if isIdSelected(idList[row], groupToId, groupList):
                for col in range(0,len(idList)):
                    if isIdSelected(idList[col], groupToId, groupList):
                        destArray[row,col] = sourceArray[row,col]
    
    # For filter 'without', find all of the values not in the specified group.
    elif args.filter == 'without':
        if len(groupList) != 1:
            print "Only one group can be specified with filter 'without'"
            exit(1)
        for row in range(0,len(idList)):
            if idList[row] not in groupToId[groupList[0]]:
                for col in range(0,len(idList)):
                    if idList[col] not in groupToId[groupList[0]]:
                        destArray[row,col] = sourceArray[row,col]

    else:
        print "Filter '%s' is not supported" %(args.filter)
        exit(1)
        
    # Open the destination file and build the header line.
    destFile = open(args.destPath, 'w')
    header = 'ID'
    for index in range(0,len(idList)):
        column = destArray[:,index]
        line = column[numpy.logical_not(column == -1.0)]
        if len(line) > 0:
            header += ','+idList[index]        
    destFile.write(header + '\n')
    
    # Write the destination matrix to the destination file.
    for index in range(0,len(idList)):
        row = destArray[index,]
        line = row[numpy.logical_not(row == -1.0)]
        if len(line) > 0:
            destFile.write(idList[index] + ',' + ','.join(['{0:g}'.format(x) for x in line]) + '\n')
    destFile.close()
            
    exit(0)
