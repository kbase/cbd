import os
import numpy
import shutil
import json
from biokbase.CompressionBasedDistance.Shock import Client as ShockClient
from biokbase.CompressionBasedDistance.Helpers import extract_seq, run_command, make_job_dir, timestamp
from biokbase.userandjobstate.client import UserAndJobState
from multiprocessing import Pool
from itertools import combinations
from biokbase import log

# String used to separate components in paired file names.
PairSeparator = '-cbdpair-'

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

# Exception thrown when sequence files have different sequence lengths.
class SeqLenError(Exception):
    pass

# Exception thrown when saving a file to Shock failed.
class ShockError(Exception):
    pass

class CompressionBasedDistance:
    
    def _cbdCalculator(self, fileList, scale, outputFile):
        # Parse the files.
        single_sizes = dict()
        pair_sizes = dict()
        
        for sourceFile in fileList:
            # Should strip prefix too
            fbase = os.path.basename(sourceFile)
            # This works as long as '.sorted.xz' only occurs at the end of the path.
            fname = fbase.replace('.sorted.xz', '')
            if PairSeparator in fname:
                pair_sizes[fname] = os.path.getsize(sourceFile)
            else:
                single_sizes[fname] = os.path.getsize(sourceFile)

        # Map file names to indices.
        fnames = single_sizes.keys()
        fnames.sort()
        indices = dict()
        
        for name,i in zip(fnames, range(len(fnames))):
            indices[name] = i
        
        # Compute the distance scores.
        pair_names = pair_sizes.keys()
        cbd_array = numpy.zeros((len(fnames), len(fnames)), dtype=float)
        for pair in pair_names:
            name1, name2 = pair.split(PairSeparator)
            c1 = float(single_sizes[name1])
            c2 = float(single_sizes[name2])
            c12 = float(pair_sizes[pair])
            distance = 1.0 - ( 2.0 * ( (c1 + c2 - c12) / (c1 + c2) ) )
            if distance > 1.0:
                part1 = "Distance %f is greater than 1.0.  " %(distance)
                part2 = "Check sequence read lengths and relative number of sequence reads.  "
                part3 = "(c1=%f %s, c2=%f %s c12=%f %s)" %(c1, name1, c2, name2, c12, pair)
                raise ValueError(part1+part2+part3)
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
    
    def _cleanup(self, input, shockClient, context, jobDirectory, pool):
        # Delete input fasta files from Shock.
        for nodeId in input['node_ids']:
            try:
                shockClient.delete(nodeId)
            except Exception as e:
                self._log(context, log.ERR, 'Error deleting node %s from Shock: %s' %(nodeId, e.message))
            
        # Remove the work directory.
        shutil.rmtree(jobDirectory)
            
        # Stop the process pool.
        pool.close()
        pool.join()
        
        return
    
    def _log(self, context, level, message):
        # Create a logger if this is the first time the method has been called.
        if self.logger is None:
            submod = os.environ.get('KB_SERVICE_NAME', 'CompressionBasedDistance')
            self.logger = log.log(submod, ip_address=True, authuser=True, module=True, method=True,
                call_id=True, config=os.getenv('KB_DEPLOYMENT_CONFIG'))

        # Log the message.
        self.logger.log_message(level, message, context['client_ip'], context['user_id'], context['module'],
                                context['method'], context['call_id'])
        return

    def __init__(self):
        self.logger = None

    def startJob(self, config, context, input):
        # Create a user and job state client and authenticate as the user.
        ujsClient = UserAndJobState(config['userandjobstate_url'], token=context['token'])

        # Create a job to track building the distance matrix.
        status = 'initializing'
        description = 'cbd-buildmatrix with %d files for user %s' %(len(input['node_ids'])+len(input['file_paths']), context['user_id'])
        progress = { 'ptype': 'task', 'max': 6 }
        job_id = ujsClient.create_and_start_job(context['token'], status, description, progress, timestamp(3600))

        # Create working directory for job and build file names.
        jobDirectory = make_job_dir(config['work_folder_path'], job_id)
        jobDataFilename = os.path.join(jobDirectory, 'jobdata.json')
        outputFilename = os.path.join(jobDirectory, 'stdout.log')
        errorFilename = os.path.join(jobDirectory, 'stderr.log')

        # Save data required for running the job.
        # Another option is to create a key of the jobid and store state.
        jobData = { 'id': job_id, 'input': input, 'context': context, 'config': config }
        json.dump(jobData, open(jobDataFilename, "w"), indent=4)

        # Start worker to run the job.
        jobScript = os.path.join(os.environ['KB_TOP'], 'bin/cbd-runjob')
        cmdline = "nohup %s %s >%s 2>%s &" %(jobScript, jobDataFilename, outputFilename, errorFilename)
        status = os.system(cmdline)
        return job_id

    def runJob(self, job):
        
        config = job['config']
        context = job['context']
        input = job['input']
        
        # Create a shock client and authenticate as the user.
        shockClient = ShockClient(config['shock_url'], context['token'])
        
        # Create a user and job state client and authenticate as the user.
        ujsClient = UserAndJobState(config['userandjobstate_url'], token=context['token'])

        # Create a process pool.
        pool = Pool(processes=int(config['num_pool_processes']))
        
        # Create a work directory for storing intermediate files.
        jobDirectory = make_job_dir(config['work_folder_path'], job['id'])

        # Download input fasta files from Shock and extract sequences to work directory.
        try:
            ujsClient.update_job_progress(job['id'], context['token'], 'extracting sequence files', 1, timestamp(3600))
        except:
            pass
        resultList = []
        sequenceList = []
        for nodeId in input['node_ids']:
            node = shockClient.get_node(nodeId)
            sourceFile = os.path.join(jobDirectory, node['file']['name'])
            destFile = '%s.sequence' %(os.path.splitext(sourceFile)[0])
            if PairSeparator in destFile: # Check for pair separator string in file name and replace as needed.
                destFile = destFile.replace(PairSeparator, '-')
            sequenceList.append(destFile)
            args = dict() # Needs to be scoped here so each process gets its own copy
            args['format'] = input['format']
            args['shockUrl'] = config['shock_url']
            args['auth'] = context['token']
            args['sequenceLen'] = input['sequence_length']
            args['minReads'] = input['min_reads']
            args['maxReads'] = input['max_reads']
            args['nodeId'] = nodeId
            args['sourceFile'] = sourceFile
            args['destFile'] = destFile
            result = pool.apply_async(extract_seq, (args,))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, context, jobDirectory, pool)
                raise ExtractError("Error extracting sequences from input sequence file, result: %d" %(result.get()))
        for path in input['file_paths']:
            sourceFile = os.path.basename(path)
            destFile = '%s/%s.sequence' %(jobDirectory, os.path.splitext(sourceFile)[0])
            if PairSeparator in destFile: # Check for pair separator string in file name and replace as needed.
                destFile = destFile.replace(PairSeparator, '-')
            sequenceList.append(destFile)
            args = dict() # Needs to be scoped here so each process gets its own copy
            args['format'] = input['format']
            args['shockUrl'] = config['shock_url']
            args['auth'] = context['token']
            args['sequenceLen'] = input['sequence_length']
            args['minReads'] = input['min_reads']
            args['maxReads'] = input['max_reads']
            args['nodeId'] = None
            args['sourceFile'] = path
            args['destFile'] = destFile
            result = pool.apply_async(extract_seq, (args,))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, context, jobDirectory, pool)
                raise ExtractError("Error extracting sequences from input sequence file, result: %d" %(result.get()))

        # Confirm that each file met the criteria for sequence length and number of sequences.
        filesToRemove = list()
        for index in range(len(sequenceList)):
            # See if the file did not have the minimum number of sequences.
            if not os.path.exists(sequenceList[index]):
                filesToRemove.append(index)
                continue

            # See if the file has no data.
            if os.path.getsize(sequenceList[index]) == 0:
                self._cleanup(input, shockClient, context, jobDirectory, pool)
                raise SeqLenError("Sequence file '%s' has no sequences" %(sequenceList[index]))

        filteredList = list()
        for index in range(len(sequenceList)):
            if index not in filesToRemove:
                filteredList.append(sequenceList[index])
        if len(filteredList) < 2:
            self._cleanup(input, shockClient, context, jobDirectory, pool)
            raise SeqLenError("There are not enough sequence files that meet the sequence length or number of sequences criteria.")

        # Sort the sequences.
        try:
            ujsClient.update_job_progress(job['id'], context['token'], 'sorting sequence files', 1, timestamp(3600))
        except:
            pass
        resultList = []
        sortedList = []
        for sourceFile in filteredList:
            destFile = '%s.sorted' %(os.path.splitext(sourceFile)[0])
            sortedList.append(destFile)
            args = [ '/usr/bin/sort', '--output=%s' %(destFile), sourceFile ]
            result = pool.apply_async(run_command, (args,))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, context, jobDirectory, pool)
                raise SortError("Error sorting sequence file, result: %d" %(result.get()))
             
        # Create combined and sorted files.
        try:
            ujsClient.update_job_progress(job['id'], context['token'], 'merging all pairs of sequence files', 1, timestamp(3600))
        except:
            pass
        resultList = []
        for p,q in combinations(sortedList, 2):
            pbase = os.path.basename(p)
            qbase = os.path.basename(q)
            dbase = '%s%s%s.sorted' %(os.path.splitext(pbase)[0], PairSeparator, os.path.splitext(qbase)[0])
            destFile = os.path.join(jobDirectory, dbase)
            sortedList.append(destFile)
            args = [ '/usr/bin/sort', '-m', '--output=%s' %(destFile), p, q ]
            result = pool.apply_async(run_command, (args,))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, context, jobDirectory, pool)
                raise MergeError("Error merging sequence files, result: %d" %(result.get()))
                   
        # Compress all sorted files.
        try:
            ujsClient.update_job_progress(job['id'], context['token'], 'compressing sequence files', 1, timestamp(3600))
        except:
            pass
        resultList = []
        compressedList = []
        for sourceFile in sortedList:
            compressedList.append(sourceFile+'.xz')
            if input['extreme']:
                level = '-9e'
            else:
                level = '-9'
            args = [ '/usr/bin/xz', '--keep', level, sourceFile ]
            result = pool.apply_async(run_command, (args,))
            resultList.append(result)
        for result in resultList:
            if result.get() != 0:
                self._cleanup(input, shockClient, context, jobDirectory, pool)
                raise CompressError("Error compressing sequence file, result: %d" %(result.get()))
        
        # Calculate the distance matrix.
        try:
            ujsClient.update_job_progress(job['id'], context['token'], 'calculating distance matrix', 1, timestamp(3600))
        except:
            pass
        csvFile = os.path.join(jobDirectory, '%s.csv' %(job['id']))
        self._cbdCalculator(compressedList, input['scale'], csvFile)
        
        # Store the output file in shock.
        try:
            ujsClient.update_job_progress(job['id'], context['token'], 'storing output file in shock', 1, timestamp(3600))
        except:
            pass
        node = shockClient.create_node(csvFile, '')
        if not node['id']:
            # Shock let us down. Save the distance matrix in the work directory for possible recovery.
            os.rename(csvFile, '%s/%s.csv' %(config['work_folder_path'], job['id']))
            self._cleanup(input, shockClient, context, jobDirectory, pool)
            raise ShockError("Error saving distance matrix file to Shock. A Shock node was not created.")
        
        # Mark the job as complete.
        results = { 'shocknodes': [ node['id'] ], 'shockurl': config['shock_url'] }
        ujsClient.complete_job(job['id'], context['token'], 'done', None, results)

        # Cleanup after ourselves.
        self._cleanup(input, shockClient, context, jobDirectory, pool)
        
        return

    def calculate(self, listFilePath, scale, csvFile):

        # Each line of the list file is a path to a compressed file.
        compressedList = list()
        listFile = open(listFilePath, 'r')
        for line in listFile:
            compressedList.append(line.strip())
        listFile.close()

        # Calculate the distance matrix.
        self._cbdCalculator(compressedList, scale, csvFile)
        return
