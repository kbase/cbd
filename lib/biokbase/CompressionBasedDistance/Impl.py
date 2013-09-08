#BEGIN_HEADER
import tempfile
import shutil
import os
import time
import numpy
from biokbase.CompressionBasedDistance.Shock import Client as ShockClient
from biokbase.CompressionBasedDistance.Helpers import extract_seq, run_command
from multiprocessing import Pool
from itertools import combinations

# Exception thrown when extract sequences failed
class ExtractError(Exception):
    pass

# Exception thrown when sorting a sequence file failed
class SortError(Exception):
    pass

# Exception thrown when merging sequence files failed
class MergeError(Exception):
    pass

# Exception thrown when compressing a sequence file failed
class CompressError(Exception):
    pass

#END_HEADER

'''

Module Name:
CompressionBasedDistance

Module Description:
Compression Based Distance (CBD) service

Compression-based distance (CBD) is a simple, rapid, and accurate method to
efficiently assess differences in microbiota samples.  CBD characterizes
the similarities between microbial communities via the amount of repetition
or overlap in order to determine microbial community distance.  CBD relies on
the fact that more repetitive data is the more it can be compressed.  By
combining 16S rRNA hypervariable tag data from different samples and assessing
the relative amounts of compression, there is a proxy for the similarities
between the communities.  The amount of compression is converted to a distance
with a minimum of 0 and a maximum of 1 by taking compression gained by combining
the datasets over the total compressed size of the individual datasets.

'''
class CompressionBasedDistance:

    #BEGIN_CLASS_HEADER
 
    def _cbdCalculator(self, fileList, scale):
        # Parse the files.
        single_sizes= dict()
        pair_sizes= dict()
        
        for sourceFile in fileList:
            # Should strip prefix too
            fbase = os.path.basename(sourceFile)
            fname = fbase.strip('.sorted.xz')
            if '.' in fname:
                pair_sizes[fname] = os.path.getsize(sourceFile)
            else:
                single_sizes[fname] = os.path.getsize(sourceFile)
                
        # Map file names to indices.
        fnames= single_sizes.keys()
        fnames.sort()
        indices= dict()
        
        for name,i in zip(fnames, range(len(fnames))):
            indices[name]= i
        
        # Compute the distance scores.
        pair_names= pair_sizes.keys()
        cbd_array= numpy.zeros((len(fnames),len(fnames)), dtype=float)
        for pair in pair_names:
            name1, name2= pair.split('.')
            c1 = single_sizes[name1]
            c2 = single_sizes[name2]
            c12 = pair_sizes[pair]
            distance= 1.0 - 2.0*(c1 + c2 - c12)/(c1 + c2)
            if scale == 'inf':
                distance = distance/(1.0 - distance)
            cbd_array[indices[name1],indices[name2]] = distance
            cbd_array[indices[name2],indices[name1]] = distance
            
        # Build the output array in CSV format.
        output = []
        output.append('ID,' + ','.join(fnames) + '\n') # first row has header
        for i in range(len(fnames)):
            output.append(fnames[i] + ',' + ','.join(['{0:g}'.format(x) for x in cbd_array[i,:]]) + '\n')
        
        return output
    
    def _cleanup(self, input, shockClient, workFolder, pool):
        # Delete input fasta files from Shock.
        for nodeId in input['node_ids']:
            shockClient.delete(nodeId)
            
        # Remove the work directory.
        if not self.config['debug']: 
            shutil.rmtree(workFolder)
            
        # Stop the process pool.
        pool.close()
        pool.join()
        
        return
    
    #END_CLASS_HEADER

    def __init__(self, config): #config contains contents of config file in hash or 
                                #None if it couldn't be found
        #BEGIN_CONSTRUCTOR
        
        if config == None:
            # There needs to be a config for the server to work.
            raise ValueError("__init__: A valid configuration was not provided.  Check KB_DEPLOYMENT_CONFIG and KB_SERVICE_NAME environment variables.")
        else:
            self.config = config
            
        # Convert flag to boolean value (a number greater than zero or the string 'True' turns the flag on).
        if self.config['debug'].isdigit():
            if int(self.config['debug']) > 0:
                self.config['debug'] = True
            else:
                self.config['debug'] = False
        else:
            if self.config['debug'] == 'True':
                self.config['debug'] = True
            else:
                self.config['debug'] = False
            
        # Create the data folder if it does not exist.
        if not os.path.exists(self.config['work_folder_path']):
            os.makedirs(self.config['work_folder_path'], 0775)

        #END_CONSTRUCTOR
        pass

    def build_matrix(self, input):
        # self.ctx is set by the wsgi application class
        # return variables are: output
        #BEGIN build_matrix
        
        print self.ctx
        
        # Create a shock client and authenticate as the user.
        shockClient = ShockClient(self.config['shock_url'], input['auth'])
        
        # Create a work directory for storing intermediate files.
        workFolder = tempfile.mkdtemp('', '', self.config["work_folder_path"])
        
        # Create a process pool.
        pool = Pool(processes=int(self.config['num_pool_processes']))
        
        # Download input fasta files from Shock and extract sequences to work directory.
        resultList = []
        sequenceList = []
        for nodeId in input['node_ids']:
            node = shockClient.get_node(nodeId)
            sourceFile = os.path.join(workFolder, node['file']['name'])
            destFile = '%s.sequence' %(os.path.splitext(sourceFile)[0])
            sequenceList.append(destFile)
            result = pool.apply_async(extract_seq, (nodeId, sourceFile, input['format'], destFile, self.config['shock_url'], input['auth'],))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, workFolder, pool)
                raise ExtractError("Error extracting sequences from input sequence file, result: %d" %(result.get()))
            
        # Sort the sequences.
        resultList = []
        sortedList = []
        for sourceFile in sequenceList:
            destFile = '%s.sorted' %(os.path.splitext(sourceFile)[0])
            sortedList.append(destFile)
            args = [ '/usr/bin/sort', '--output=%s' %(destFile), sourceFile ]
            result = pool.apply_async(run_command, (args,))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, workFolder, pool)
                raise SortError("Error sorting sequence file, result: %d" %(result.get()))
             
        # Create combined and sorted files.   
        resultList = []
        for p,q in combinations(sortedList, 2):
            pbase = os.path.basename(p)
            qbase = os.path.basename(q)
            dbase = '%s.%s.sorted' %(os.path.splitext(pbase)[0], os.path.splitext(qbase)[0])
            destFile = os.path.join(workFolder, dbase)
            sortedList.append(destFile)
            args = [ '/usr/bin/sort', '-m', '--output=%s' %(destFile), p, q ]
            result = pool.apply_async(run_command, (args,))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, workFolder, pool)
                raise MergeError("Error merging sequence files, result: %d" %(result.get()))
                   
        # Compress all sorted files
        resultList = []
        compressedList = []
        for sourceFile in sortedList:
            compressedList.append(sourceFile+'.xz')
            args = [ '/usr/bin/xz', '--keep', '-9e', sourceFile ]
            result = pool.apply_async(run_command, (args,))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, workFolder, pool)
                raise CompressError("Error compressing sequence file, result: %d" %(result.get()))
        
        # Calculate
        output = self._cbdCalculator(compressedList, input['scale'])
        
        # Cleanup after ourselves.
        self._cleanup(input, shockClient, workFolder, pool)
        
        #END build_matrix

        #At some point might do deeper type checking...
        if not isinstance(output, list):
            raise ValueError('Method build_matrix return value output is not type list as required.')
        # return the results
        return [ output ]
        
