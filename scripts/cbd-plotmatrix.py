import argparse
import sys
import os
import numpy
from cogent.cluster.UPGMA import upgma
from cogent.phylo.nj import nj
import matplotlib
from scipy.cluster.hierarchy import dendrogram, linkage
import scipy.spatial.distance as ssd
import rpy2.robjects as ro

desc1 = '''
NAME
      cbd-plotmatrix -- generate a plot of a distance matrix 

SYNOPSIS      
'''

desc2 = '''
DESCRIPTION
      Generate a plot to visualize the relationship between entries in a
      distance matrix.

      The sourcePath positional argument is the path to the source distance
      matrix saved by cbd-getmatrix or cbd-filtermatrix.

      The destPath positional argument is the path to the output file
      containing the plot.

      The --type optional argument specifies the type of the plot.  Valid
      types are 'tree' to generate a tree plot, 'dendrogram' to generate a
      dendrogram plot, and 'mds' to generate a metric dimensional scaling plot.
      The default type is 'tree'.

      For a 'tree' type of plot, the supported optional argument is --method.
      The --method optional argument specifies the clustering method to use and
      the valid values are 'upgma' for unweighted pair group method with
      arithmetic mean and 'nj' for neighbor joining.  The default method is
      'upgma'.  All other optional arguments are ignored.

      For a 'dendrogram' type of plot, the supported optional arguments are
      --method, --title, --labels, and --plot-options.  The --method optional
      argument specifies the clustering method to use and the valid values are
      'complete', 'upgma', 'single', 'weighted', 'centroid', 'median', or
      'ward'.  The default method is complete.  The --title optional argument
      specifies the title to place on the plot.  The default title is
      'Dendrogram'.  The --labels optional argument specifies the source for
      labeling the leaves in the dendrogram.  The valid values are 'input' to
      use the value from the third field of the input list file and 'source'
      to use the headings from the source distance matrix.  The default value
      is 'source'.  The --input-file-path optional argument must be specified
      when using 'input' for the labels.  The --plot-options optional argument
      specifies a semicolon delimited list of options for controlling the plot.
      The valid options are 'labelsize', 'count_sort', and 'orientation'.

      For a 'mds' type of plot, the supported optional arguments are --title,
      --labels, --colors, --file-options, --plot-options.  The --title optional
      argument specifies the title to place on the plot.  The default title is
      'MDS'.  The --labels optional argument specifies the source for labeling
      the points in the plot.  The valid values are 'input' to use the value
      from the third field of the input list file, 'source' to use the headings
      from the source distance matrix, and 'none' for no labels.  The default
      value is 'source'.  The --input-file-path optional argument must be
      specified when using 'input' for the labels.  The --file-options optional
      argument specifies a semicolon delimited list of options for controlling
      the output file.  Any options supported by the R pdf() function can be
      used.  The --plot-options optional argument specifies a semicolon
      delimited list of options for controlling the plot.  Any options supported
      by the R plot() function can be used.  Options that start with 'text.' are
      used to control the text labels on the plot.  The --colors optional
      argument is a semicolon delimited list of groups and colors.  A point from
      a sample with the specified group is drawn with the specified color.  The
      default color is black.  The --input-file-path optional argument must be
      specified when using the --colors optional argument.

'''

desc3 = '''
EXAMPLES
      Generate a tree plot using the upgma method:
      > cbd-plotmatrix mystudy.csv mystudy.txt

      Generate a tree plot using the nj method:
      > cbd-plotmatrix --method nj mystudy.csv mystudy.txt

      Generate a dendrogram plot using the centroid method and with a title:
      > cbd-plotmatrix --type dendrogram --method centroid --title 'My Plot'
          --plot-options label_size=8 mystudy.csv mystudy.pdf

      Generate a MDS plot using the input list file for the labels:
      > cbd-plotmatrix --type mds --labels input --input-file-path mystudy.list
          --file-options 'height=5.0;width=5.0' --plot-options 'pch=19;text.col=blue'
          --colors 'day1=blue;day7=orange' mystudy.csv mystudy.pdf

SEE ALSO
      cbd-buildmatrix
      cbd-getmatrix
      cbd-filtermatrix

AUTHORS
      Mike Mundy 
'''

def get_fields_from_line(line):
    line = line.strip('\n\r')
    if line and line[0] != '#': # Skip empty and comment lines
        fields = line.split('\t')
        if len(fields) < 2 or len(fields) > 3:
            print "Each line must contain a path and group list and optional label.  The following line contains %d fields:" %(len(fields))
            print "  " + line
            exit(1)

        # Extract the sampleID from the path in the first field.
        fileName = os.path.basename(fields[0])
        sampleID = os.path.splitext(fileName)[0]

        # Create a list of groups from the semicolon delimited string in the second field.
        groups = fields[1].split(';')

        # The label in the third field is optional.
        if len(fields) > 2:
            label = fields[2]
        else:
            label = ''
        return (sampleID, groups, label)
    else:
        return (None, None, None)

def plot_tree(sourceArray, args):

    # Build the input dictionary for the tree functions.
    distanceDict = dict()
    for i in range(len(idList)):
        for j in range(len(idList)):
            distanceDict[(idList[i], idList[j])]=sourceArray[i,j]

    # Generate the tree using the specified method.
    if args.method == 'upgma' or args.method is None:
        tree = upgma(distanceDict)
    elif args.method == 'nj':
        tree = nj(distanceDict)
    else:
        print "Method '%s' is not supported." %(args.method)
        exit(1)

    # Convert the tree to text and save to the specified file.
    art = tree.asciiArt()
    destFile = open(args.destPath, 'w')
    destFile.write(art+'\n')
    destFile.close()
    return

def plot_dendrogram(sourceArray, idList, args):

    # Convert input value to dendrogram() function value and set default.
    if args.method is None:
        args.method = 'complete'
    if args.method == 'upgma':
        args.method = 'average'

    # Convert the redundant square matrix form into a condensed nC2 array and
    # build the linkage matrix using the specified method.
    distArray = ssd.squareform(sourceArray)
    linkageMatrix = linkage(distArray, args.method)

    # Set the labels for the plot.
    if args.labels == 'input':
        # Use the labels from the input list file.
        if args.inputFilePath is None:
            print "You must use the --input-file-path argument when using the --labels input argument."
            exit(1)

        # Open the input file with the list of sequence files, groups, and labels.
        try:
            inputFile = open(args.inputFilePath, 'r')
        except IOError as e:
            print "Error opening input list file '%s': %s" %(args.inputFilePath, e.strerror)
            exit(1)

        # Build a dictionary that maps sample IDs to labels.
        idToLabel = dict()
        for line in inputFile:
            (sampleID, groups, label) = get_fields_from_line(line)
            if sampleID is not None:
                idToLabel[sampleID] = label
        inputFile.close()

        # Build the list of labels in the same order as the distance matrix.
        labelList = list()
        for index in range(len(idList)):
            labelList.append(idToLabel[idList[index]])

    elif args.labels == 'source':
        # Use the sample IDs from the source distance matrix for the labels.
        labelList = idList

    else:
        print "Label type '%s' is not supported." %(args.labels)
        exit(1)

    # Parse the options customize the plot.
    plotOptions = dict()
    if args.plotOptions is not None:
        optionList = args.plotOptions.split(';')
        for index in range(len(optionList)):
            fields = optionList[index].split('=')
            try:
                plotOptions[fields[0]] = float(fields[1])
            except:
                plotOptions[fields[0]] = fields[1]

    # Add default options if they haven't been overridden by the user.
    if 'labelsize' not in plotOptions:
        plotOptions['labelsize'] = 10
    if 'count_sort' not in plotOptions:
        plotOptions['count_sort'] = 'ascending'
    if 'orientation' not in plotOptions:
        plotOptions['orientation'] = 'right'

    # Generate the plot and save to file.
    matplotlib.use('Agg')
    dendrogram(linkageMatrix, labels=labelList, count_sort=plotOptions['count_sort'], orientation=plotOptions['orientation'])
    matplotlib.pyplot.title(args.title)
    if plotOptions['orientation'] == 'left' or plotOptions['orientation'] == 'right':
        tickAxis = 'y'
    else:
        tickAxis = 'x'
    matplotlib.pyplot.tick_params(tickAxis, labelsize=plotOptions['labelsize']) # Need to do this manually because of bug in dendrogram() function
    matplotlib.pyplot.savefig(args.destPath)
    return

def plot_mds(idList, args):

    # Set the colors for the plot.
    if args.colors is not None or args.labels == 'input':
        if args.inputFilePath is None:
            print "You must use the --input-file-path argument when using the --colors argument."
            exit(1)

        # Parse the colors argument which assigns a color to a group.
        groupToColor = dict()
        if args.colors is not None:
            itemList = args.colors.split(';') # Each group=color item is delimited by a semicolon
            for index in range(len(itemList)):
                pair = itemList[index].split('=')
                groupToColor[pair[0]] = pair[1]
            if len(groupToColor) == 0:
                print "Error parsing colors argument '%s'" %(args.colors)
                exit(1)

        # Open the input file with the list of sequence files, groups, and labels.
        try:
            inputFile = open(args.inputFilePath, 'r')
        except IOError as e:
            print "Error opening input list file '%s': %s" %(args.inputPath, e.strerror)
            exit(1)

        # Parse the list file and keep track of the groups assigned to each ID and an
        # optional label for the ID.
        idToGroups = dict()
        idToLabel = dict()
        for line in inputFile:
            (sampleID, groups, label) = get_fields_from_line(line)
            if sampleID is not None:
                # Add an entry to the dictionary for the ID.
                idToGroups[sampleID] = groups
                idToLabel[sampleID] = label
        inputFile.close()

        # Assign colors and labels for each sample ID.
        labelList = list()
        colorList = list()
        for index in range(len(idList)):
            groupList = idToGroups[idList[index]]
            addedGroup = False
            for group in groupList:
                if group in groupToColor:
                    colorList.append(groupToColor[group])
                    addedGroup = True
            if not addedGroup:
                colorList.append('black')
            labelList.append(idToLabel[idList[index]])

    if args.colors is None:
        # Default is for every point to be black.
        colorList = [ 'black' ]

    if args.labels == 'source':
        # Use the sample IDs from the source distance matrix for the labels.
        labelList = idList

    elif args.labels != 'input' and args.labels != 'none':
        print "Label type '%s' is not supported." %(args.labels)
        exit(1)

    # Run the R commands to create the points for the MDS plot.
    ro.r('input.data <- read.csv("%s")' %(args.sourcePath))
    ro.r('distance.matrix <- as.matrix(input.data[,-1])')
    ro.r('fit <- cmdscale(distance.matrix, eig=TRUE, k=2)')
    x = ro.r('fit$points[,1]')
    y = ro.r('fit$points[,2]')

    # Parse the options to pass to the pdf command.
    fileArgs = dict()
    if args.fileOptions is not None:
        optionList = args.fileOptions.split(';')
        for index in range(len(optionList)):
            fields = optionList[index].split('=')
            try:
                fileArgs[fields[0]] = float(fields[1])
            except:
                fileArgs[fields[0]] = fields[1]

    # Open the pdf device.
    ro.r.pdf(args.destPath, **fileArgs)

    # Parse the options for creating the plot.
    plotArgs = dict()
    textArgs = dict()
    if args.plotOptions is not None:
        optionList = args.plotOptions.split(';')
        for index in range(len(optionList)):
            fields = optionList[index].split('=')
            try:
                value = float(fields[1])
            except:
                value = fields[1]
            if fields[0].startswith('text.'):
                keyword = fields[0].lstrip('text.')
                textArgs[keyword] = value
            else:
                plotArgs[fields[0]] = value

    # Add default options if they haven't been overridden by the user.
    if 'xlab' not in plotArgs:
        plotArgs['xlab'] = 'Coordinate 1'
    if 'ylab' not in plotArgs:
        plotArgs['ylab'] = 'Coordinate 2'
    if 'type' not in plotArgs:
        plotArgs['type'] = 'p'
    if 'pch' not in plotArgs:
        plotArgs['pch'] = 17
    plotArgs['main'] = args.title
    colors = ro.StrVector(colorList)
    labels = ro.StrVector(labelList)

    # Generate the plot and save to file.
    ro.r.plot(x, y, col=colors, **plotArgs)
    ro.r.abline(h=0, v=0)

    # Add labels to the points.
    if args.labels != 'none':
        if 'pos' not in textArgs:
            textArgs['pos'] = 3
        if 'cex' not in textArgs:
            textArgs['cex'] = 0.5
        ro.r.text(x, y, labels = labels, **textArgs)
    ro.r('dev.off()')
    return

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='cbd-plotmatrix', epilog=desc3)
    parser.add_argument('sourcePath', help='path to source distance matrix file', action='store', default=None)
    parser.add_argument('destPath', help='path to destination distance matrix file', action='store', default=None)
    parser.add_argument('--type', help='type of plot to generate', action='store', dest='type', default='tree')
    parser.add_argument('--method', help='clustering method', action='store', dest='method', default=None)
    parser.add_argument('--title', help='title for plot', action='store', dest='title', default=None)
    parser.add_argument('--colors', help='assign colors to groups', action='store', dest='colors', default=None)
    parser.add_argument('--input-file-path', help='path to file with list of input sequence files', action='store', dest='inputFilePath', default=None)
    parser.add_argument('--labels', help='source for labels on points in plot', dest='labels', action='store', default='source')
    parser.add_argument('--plot-options', help='options to pass to plot command', action='store', dest='plotOptions', default=None)
    parser.add_argument('--file-options', help='options to pass to file creation command', action='store', dest='fileOptions', default=None)
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()
    
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
            sourceArray[row,index] = float(fields[index]) * float(fields[index])
        row += 1
    sourceFile.close()
    
    # Create the specified plot.
    if args.type == 'tree':
        plot_tree(sourceArray, args)

    elif args.type == 'dendrogram':
        if args.title is None:
            args.title = 'Dendrogram'
        plot_dendrogram(sourceArray, idList, args)

    elif args.type == 'mds':
        if args.title is None:
            args.title = 'MDS'
        plot_mds(idList, args)

    else:
        print "Plot type '%s' is not supported" %(args.type)
        exit(1)
        
    exit(0)
