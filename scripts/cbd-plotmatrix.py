import argparse
import sys
import os
import numpy
from cogent.cluster.UPGMA import upgma
from cogent.phylo.nj import nj
#import networkx

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
      matrix created by cbd-buildmatrix and saved by cbd-getmatrix.

      The destPath positional argument is the path to the output file
      containing the plot.

      The --type optional argument specifies the type of the plot.  Valid
      types are 'upgma' to generate a tree using the unweighted pair group
      method with arithmetic mean algorithm, or 'nj' to generate a tree using
      the neighbor joining algorithm.
'''

desc3 = '''
EXAMPLES
      Generate a plot using the upgma algorithm:
      > cbd-plotmatrix mystudy.csv mystudy.txt

      Generate a plot using the nj algorithm:
      > cbd-plotmatrix --type nj mystudy.csv mystudy.txt

SEE ALSO
      cbd-buildmatrix
      cbd-getmatrix
      cbd-filtermatrix

AUTHORS
      Mike Mundy 
'''

if __name__ == "__main__":
    # Parse options.
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='cbd_filtermatrix', epilog=desc3)
    parser.add_argument('sourcePath', help='path to source distance matrix file', action='store', default=None)
    parser.add_argument('destPath', help='path to destination distance matrix file', action='store', default=None)
    parser.add_argument('--type', help='type of plot to generate', action='store', dest='type', default='upgma')
#    parser.add_argument('--scale', help='factor used to scale matrix values', action='store', dest='scale', type=float, default=10.0)
#    parser.add_argument('--node-color', help='color of nodes in network plot', action='store', dest='nodeColor', default='red')
#    parser.add_argument('--edge-color', help='color of edges in network plot', action='store', dest='edgeColor', default='blue')
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
            sourceArray[row,index] = float(fields[index])
        row += 1
    sourceFile.close()
    
    if args.type == 'upgma':
        distanceDict = dict()
        for i in range(len(idList)):
            for j in range(len(idList)):
                distanceDict[(idList[i], idList[j])]=sourceArray[i,j]
        tree = upgma(distanceDict)
        art = tree.asciiArt()
        destFile = open(args.destPath, 'w')
        destFile.write(art+'\n')
        destFile.close()
        
    elif args.type == 'nj':
        distanceDict = dict()
        for i in range(len(idList)):
            for j in range(len(idList)):
                distanceDict[(idList[i], idList[j])]=sourceArray[i,j]
        tree = nj(distanceDict)
        art = tree.asciiArt()
        destFile = open(args.destPath, 'w')
        destFile.write(art+'\n')
        destFile.close()
        
#     elif args.type == 'network':
#         dt = [('len', float)]
#         sourceArray = sourceArray.view(dt)
#         
#         # Build the graph and label the nodes from the IDs in the source file.
#         graph = networkx.from_numpy_matrix(sourceArray)
#         graph = networkx.relabel_nodes(graph, dict(zip(range(len(graph.nodes())),idList)))    
#         graphviz = networkx.to_agraph(graph)
#         
#         # Set the color of the nodes and edges.
#         graphviz.node_attr.update(color=args.nodeColor, style='filled')
#         graphviz.edge_attr.update(color=args.edgeColor, width='2.0')
#         
#         # Draw the graph and save to the specified file.
#         graphviz.draw(args.destPath, format='png', prog='neato')
      
    else:
        print "Plot type '%s' is not supported" %(args.type)
        exit(1)
        
    exit(0)
