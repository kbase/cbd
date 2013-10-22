import os
import numpy
import shutil
from biokbase.CompressionBasedDistance.Shock import Client as ShockClient
from biokbase.CompressionBasedDistance.Helpers import extract_seq, run_command, make_job_dir, timestamp
from biokbase.userandjobstate.client import UserAndJobState
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

class CompressionBasedDistance:
    
    def _cbdCalculator(self, fileList, scale, outputFile):
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
            
        # Build the output file in CSV format.
        outf = open(outputFile, 'w')
        outf.write('ID,' + ','.join(fnames) + '\n')
        for i in range(len(fnames)):
             outf.write(fnames[i] + ',' + ','.join(['{0:g}'.format(x) for x in cbd_array[i,:]]) + '\n')
        outf.close()
        return
    
    def _cleanup(self, input, shockClient, jobDirectory, pool):
        # Delete input fasta files from Shock.
        for nodeId in input['node_ids']:
            shockClient.delete(nodeId)
            
        # Remove the work directory.
        if self.config['debug'] == '0': 
            shutil.rmtree(jobDirectory)
        else:
            print "skipped rmtree"
            
        # Stop the process pool.
        pool.close()
        pool.join()
        
        return
    
    def runJob(self, job):
        
        self.config = job['config']
        self.ctx = job['context']
        input = job['input']
        
        # Create a shock client and authenticate as the user.
        shockClient = ShockClient(self.config['shock_url'], self.ctx['token'])
        
        # Create a user and job state client and authenticate as the user.
        ujsClient = UserAndJobState(self.config['userandjobstate_url'], token=self.ctx['token'])

        # Create a process pool.
        pool = Pool(processes=int(self.config['num_pool_processes']))
        
        # Create a work directory for storing intermediate files.
        jobDirectory = make_job_dir(self.config['work_folder_path'], job['id'])

        # Download input fasta files from Shock and extract sequences to work directory.
        ujsClient.update_job_progress(job['id'], self.ctx['token'], 'extracting sequence files', 1, timestamp(3600))
        resultList = []
        sequenceList = []
        for nodeId in input['node_ids']:
            node = shockClient.get_node(nodeId)
            sourceFile = os.path.join(jobDirectory, node['file']['name'])
            destFile = '%s.sequence' %(os.path.splitext(sourceFile)[0])
            sequenceList.append(destFile)
            result = pool.apply_async(extract_seq, (nodeId, sourceFile, input['format'], destFile, self.config['shock_url'], self.ctx['token'],))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, jobDirectory, pool)
                raise ExtractError("Error extracting sequences from input sequence file, result: %d" %(result.get()))
            
        # Sort the sequences.
        ujsClient.update_job_progress(job['id'], self.ctx['token'], 'sorting sequence files', 1, timestamp(3600))
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
                self._cleanup(input, shockClient, jobDirectory, pool)
                raise SortError("Error sorting sequence file, result: %d" %(result.get()))
             
        # Create combined and sorted files.
        ujsClient.update_job_progress(job['id'], self.ctx['token'], 'merging and sorting sequence files', 1, timestamp(3600))
        resultList = []
        for p,q in combinations(sortedList, 2):
            pbase = os.path.basename(p)
            qbase = os.path.basename(q)
            dbase = '%s.%s.sorted' %(os.path.splitext(pbase)[0], os.path.splitext(qbase)[0])
            destFile = os.path.join(jobDirectory, dbase)
            sortedList.append(destFile)
            args = [ '/usr/bin/sort', '-m', '--output=%s' %(destFile), p, q ]
            result = pool.apply_async(run_command, (args,))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, jobDirectory, pool)
                raise MergeError("Error merging sequence files, result: %d" %(result.get()))
                   
        # Compress all sorted files.
        ujsClient.update_job_progress(job['id'], self.ctx['token'], 'compressing sequence files', 1, timestamp(3600))
        resultList = []
        compressedList = []
        for sourceFile in sortedList:
            compressedList.append(sourceFile+'.xz')
            args = [ '/usr/bin/xz', '--keep', '-9e', sourceFile ]
            result = pool.apply_async(run_command, (args,))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, jobDirectory, pool)
                raise CompressError("Error compressing sequence file, result: %d" %(result.get()))
        
        # Calculate the distance matrix.
        ujsClient.update_job_progress(job['id'], self.ctx['token'], 'calculating distance matrix', 1, timestamp(3600))
        csvFile = os.path.join(jobDirectory, 'output.csv')
        self._cbdCalculator(compressedList, input['scale'], csvFile)
        
        # Store the output file in shock
        ujsClient.update_job_progress(job['id'], self.ctx['token'], 'storing output file in shock', 1, timestamp(3600))
        node = shockClient.create_node(csvFile, '')
        
        # Mark the job as complete.
        results = { 'shocknodes': [ node['id'] ], 'shockurl': self.config['shock_url'] }
        ujsClient.complete_job(job['id'], self.ctx['token'], 'done', '', results)

        # Cleanup after ourselves.
        self._cleanup(input, shockClient, jobDirectory, pool)
        
        return
