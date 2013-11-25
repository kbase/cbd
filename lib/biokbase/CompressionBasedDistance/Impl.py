#BEGIN_HEADER
import os
import json
from biokbase.userandjobstate.client import UserAndJobState
from biokbase.CompressionBasedDistance.Helpers import make_job_dir, timestamp
#END_HEADER


class CompressionBasedDistance:
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
by taking compression gained by combining the datasets over the total
compressed size of the individual datasets.  The distance has a value with a
minimum of 0 meaning the communities are the same and a maximum of 1 meaning
the communities are completely different.
    '''

    ######## WARNING FOR GEVENT USERS #######
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    #########################################
    #BEGIN_CLASS_HEADER
 
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
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

        # Create the work folder if it does not exist.
        if not os.path.exists(self.config['work_folder_path']):
            os.makedirs(self.config['work_folder_path'], 0775)

        #END_CONSTRUCTOR
        pass

    def build_matrix(self, input):
        # self.ctx is set by the wsgi application class
        # return variables are: job_id
        #BEGIN build_matrix
        
        # Create a user and job state client and authenticate as the user.
        ujsClient = UserAndJobState(self.config['userandjobstate_url'], token=self.ctx['token'])
        
        # Create a job to track building the distance matrix.
        status = 'initializing'
        description = 'cbd-buildmatrix with %d files for user ' %(len(input['node_ids']))
        progress = { 'ptype': 'task', 'max': 6 }
        job_id = ujsClient.create_and_start_job(self.ctx['token'], status, description, progress, timestamp(3600))

        # Create working directory for job and build file names.
        jobDirectory = make_job_dir(self.config['work_folder_path'], job_id)
        jobDataFilename = os.path.join(jobDirectory, 'jobdata.json')
        outputFilename = os.path.join(jobDirectory, 'stdout.log')
        errorFilename = os.path.join(jobDirectory, 'stderr.log')
        
        # Save data required for running the job.
        # Another option is to create a key of the jobid and store state.
        jobData = { 'id': job_id, 'input': input, 'context': self.ctx, 'config': self.config }
        json.dump(jobData, open(jobDataFilename, "w"), indent=4)

        # Start worker to run the job.
        jobScript = os.path.join(os.environ['KB_TOP'], 'bin/cbd-runjob')
        cmdline = "nohup %s %s >%s 2>%s &" %(jobScript, jobDataFilename, outputFilename, errorFilename)
        status = os.system(cmdline)

        #END build_matrix

        #At some point might do deeper type checking...
        if not isinstance(job_id, basestring):
            raise ValueError('Method build_matrix return value ' +
                             'job_id is not type basestring as required.')
        # return the results
        return [job_id]
