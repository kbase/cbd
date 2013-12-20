#! /usr/bin/python

import os
import subprocess
import sys
import time
from biokbase.CompressionBasedDistance.Shock import Client as ShockClient
from ConfigParser import ConfigParser
from Bio import SeqIO

# Exception thrown when a command failed
class CommandError(Exception):
    pass

DefaultURL = 'http://kbase.us/services/cbd/'

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

def extract_seq(nodeId, sourceFile, format, destFile, shockUrl, auth):
    # Download the file from Shock to the working directory.
    if nodeId is not None:
        shockClient = ShockClient(shockUrl, auth)
        shockClient.download_to_path(nodeId, sourceFile)

    # Extract the sequences from the source file.
    with open(destFile, 'w') as f:
        for seqRecord in SeqIO.parse(sourceFile, format):
            f.write(str(seqRecord.seq) + '\n')
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
