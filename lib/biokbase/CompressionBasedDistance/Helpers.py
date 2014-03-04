#! /usr/bin/python

import os
import subprocess
import sys
import time
import json
from shock import Client as ShockClient
from biokbase.userandjobstate.client import UserAndJobState
from ConfigParser import ConfigParser
from Bio import SeqIO

# Exception thrown when a command failed
class CommandError(Exception):
    pass

DefaultURL = 'https://kbase.us/services/cbd/'

def get_url():
    if 'KB_RUNNING_IN_IRIS' not in os.environ:
        filename = os.path.join(os.environ['HOME'], '.kbase_cbdURL')
    else:
        filename = '/.kbase_cbdURL'
    if os.path.exists(filename):
        fid = open(filename, 'r')
        currentURL = fid.readline()
        currentURL.strip()
        fid.close()
    else:
        currentURL = DefaultURL;
    return currentURL

def set_url(newURL):
    if newURL ==  'default':
        newURL = DefaultURL
    if 'KB_RUNNING_IN_IRIS' not in os.environ:
        filename = os.path.join(os.environ['HOME'], '.kbase_cbdURL')
    else:
        filename = '/.kbase_cbdURL'
    fid = open(filename, 'w')
    fid.write(newURL)
    fid.close()
    return newURL
    
def get_config(filename):
    # Use default config file if one is not specified.
    if filename == None:
        filename = os.path.join(os.environ['KB_TOP'], 'deployment.cfg')
        
    # Read the config file and extract the probabilistic annotation section.
    retconfig = {}
    config = ConfigParser()
    config.read(filename)
    for nameval in config.items('CompressionBasedDistance'):
        retconfig[nameval[0]] = nameval[1]
    return retconfig

def make_job_dir(workDirectory, jobID):
    jobDirectory = os.path.join(workDirectory, jobID)
    if not os.path.exists(jobDirectory):
        os.makedirs(jobDirectory, 0775)
    return jobDirectory

def extract_seq(args):
    # Download the file from Shock to the working directory.
    if args['nodeId'] is not None:
        shockClient = ShockClient(args['shockUrl'], args['auth'])
        shockClient.download_to_path(args['nodeId'], args['sourceFile'])

    # Extract the sequences from the source file.
    numReads = 0
    with open(args['destFile'], 'w') as f:
        if args['sequenceLen'] > 0: # A length to trim to was specified
            for seqRecord in SeqIO.parse(args['sourceFile'], args['format']):
                seq = str(seqRecord.seq)
                if len(seq) < args['sequenceLen']:
                    continue
                if len(seq) > args['sequenceLen']:
                    seq = seq[:args['sequenceLen']]
                f.write(str(seq) + '\n')
                numReads += 1
                if numReads == args['maxReads']:
                    break
        elif args['maxReads'] > 0:
            for seqRecord in SeqIO.parse(args['sourceFile'], args['format']):
                f.write(str(seqRecord.seq) + '\n')
                numReads += 1
                if numReads == args['maxReads']:
                    break
        else:
            for seqRecord in SeqIO.parse(args['sourceFile'], args['format']):
                f.write(str(seqRecord.seq) + '\n')

    # Delete the file if it does not have enough reads.
    if args['minReads'] > 0 and numReads < args['minReads']:
        os.remove(args['destFile'])
    return 0

''' Run a command in a new process. '''

def run_command(args):
    try:
        retcode = subprocess.call(args)
        if retcode < 0:
            cmd = ' '.join(args)
            raise CommandError("'%s' was terminated by signal %d" %(cmd, -retcode))
        else:
            if retcode > 0:
                cmd = ' '.join(args)
                raise CommandError("'%s' failed with status %d" %(cmd, retcode))
    except OSError as e:
        cmd = ' '.join(args)
        raise CommandError("Failed to run '%s': %s" %(cmd, e.strerror))
    return 0

''' Get a timestamp in the format required by user and job state service.
    Add deltaSeconds to the current time to get a time in the future. '''

def timestamp(deltaSeconds):
    # Just UTC timestamps to avoid timezone issues.
    now = time.time() + deltaSeconds
    ts = time.gmtime(time.time() + deltaSeconds)
    return time.strftime('%Y-%m-%dT%H:%M:%S+0000', ts)

''' Convert a job info tuple into a dictionary. '''

def job_info_dict(infoTuple):
    info = dict()
    info['id'] = infoTuple[0]
    info['service'] = infoTuple[1]
    info['stage'] = infoTuple[2]
    info['started'] = infoTuple[3]
    info['status'] = infoTuple[4]
    info['last_update'] = infoTuple[5]
    info['total_progress'] = infoTuple[6]
    info['max_progress'] = infoTuple[7]
    info['progress_type'] = infoTuple[8]
    info['est_complete'] = infoTuple[9]
    info['complete'] = infoTuple[10]
    info['error'] = infoTuple[11]
    info['description'] = infoTuple[12]
    info['results'] = infoTuple[13]
    return info

''' Parse the input file for building a matrix. '''

def parse_input_file(inputPath):
    # Open the input file with the list of files.
    try:
        infile = open(inputPath, "r")
    except IOError as e:
        print "Error opening input list file '%s': %s" %(inputPath, e.strerror)
        return None, None, 1

    # Make sure all of the files in the list of files exist.
    numMissingFiles = 0
    fileList = list()
    extensions = dict()
    for line in infile:
        line = line.strip('\n\r')
        if line and line[0] != '#': # Skip empty lines
            fields = line.split('\t')
            filename = fields[0]
            if os.path.isfile(filename):
                fileList.append(filename)
                ext = os.path.splitext(filename)[1].split('.')[-1]
                extensions[ext] = 1
            else:
                print "'%s' does not exist" %(filename)
                numMissingFiles += 1
    infile.close()
    if numMissingFiles > 0:
        print "%d files are not accessible. Update %s with correct file names" %(numMissingFiles, inputPath)

    return fileList, extensions, numMissingFiles

def start_job(config, context, input):
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
