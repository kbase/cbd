#! /usr/bin/python

import os
import subprocess
import sys
from biokbase.CompressionBasedDistance.Shock import Client as ShockClient
from ConfigParser import ConfigParser
from Bio import SeqIO

DefaultURL = "http://kbase.us/services/CompressionBasedDistance/"

def get_url():
    if "KB_RUNNING_IN_IRIS" not in os.environ:
        filename = os.path.join(os.environ["HOME"], ".kbase_cbdURL")
        if os.path.exists(filename):
            fid = open(filename, "r")
            currentURL = fid.readline()
            currentURL.strip()
            fid.close()
        else:
            currentURL = DefaultURL;
    elif "KB_CBDURL" in os.environ:
        currentURL = os.environ["KB_CBDURL"]
    else:
        currentURL = DefaultURL
    return currentURL

def set_url(newURL):
    if newURL ==  "default":
        newURL = DefaultURL
    if "KB_RUNNING_IN_IRIS" not in os.environ:
        fid = open(os.path.join(os.environ["HOME"], ".kbase_cbdURL"), "w")
        fid.write(newURL)
        fid.close()
    else:
        os.environ["KB_CBDURL"] = newURL
    return newURL
    
def get_auth_token():
    token = None
    if "KB_RUNNING_IN_IRIS" not in os.environ:
        filename = os.path.join(os.environ["HOME"], ".kbase_auth")
        if os.path.exists(filename):
            fid = open(filename, "r")
            token = fid.readline()
            token.strip()
            fid.close()
    else:
        token = os.environ["KB_AUTH_TOKEN"]
    return token

def get_config(filename):
    # Use default config file if one is not specified.
    if filename == None:
        filename = os.path.join(sys.environ["KB_TOP"], "deployment.cfg")
        
    # Read the config file and extract the probabilistic annotation section.
    retconfig = {}
    config = ConfigParser()
    config.read(filename)
    for nameval in config.items("CompressionBasedDistance"):
        retconfig[nameval[0]] = nameval[1]
    return retconfig

def make_job_dir(workDirectory, jobID):
    jobDirectory = os.path.join(workDirectory, jobID)
    if not os.path.exists(jobDirectory):
        os.makedirs(jobDirectory, 0775)
    return jobDirectory

def extract_seq(nodeId, sourceFile, format, destFile, shockUrl, auth):
    # Download the file from Shock to the working directory.
    shockClient = ShockClient(shockUrl, auth)
    shockClient.download_to_path(nodeId, sourceFile)

    # Extract the sequences from the source file.
    with open(destFile, 'w') as f:
        for seqRecord in SeqIO.parse(sourceFile, format):
            f.write(str(seqRecord.seq) + '\n')
    return 0

def run_command(args):
    try:
        retcode = subprocess.call(args)
        if retcode < 0:
            cmd = ' '.join(args)
#            raise MakeblastdbError("'%s' was terminated by signal %d" %(cmd, -retcode))
            return 1
        else:
            if retcode > 0:
                cmd = ' '.join(args)
#                raise MakeblastdbError("'%s' failed with status %d" %(cmd, retcode))
                return 1
    except OSError as e:
        cmd = ' '.join(args)
#        raise MakeblastdbError("Failed to run '%s': %s" %(cmd, e.strerror))
        return 1
    return 0
