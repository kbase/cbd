#BEGIN_HEADER
import os
from biokbase.userandjobstate.client import UserAndJobState
from biokbase.CompressionBasedDistance.Helpers import start_job
from biokbase import log

VERSION = '1.4'
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
            
        # Create the work folder if it does not exist.
        if not os.path.exists(self.config['work_folder_path']):
            os.makedirs(self.config['work_folder_path'], 0775)

        # Log info about the server configuration (need to create our own logger object since
        # we do not have a context during initialization).
        submod = os.environ.get('KB_SERVICE_NAME', 'CompressionBasedDistance')
        mylog = log.log(submod, ip_address=True, authuser=True, module=True, method=True,
            call_id=True, config=os.getenv('KB_DEPLOYMENT_CONFIG'))
        mylog.log_message(log.INFO, 'Server started, version is '+VERSION)
        configValues = 'shock_url='+self.config['shock_url']+', userandjobstate_url='+self.config['userandjobstate_url']
        configValues += ', work_folder_path='+self.config['work_folder_path']+', num_pool_processes='+self.config['num_pool_processes']
        mylog.log_message(log.INFO, configValues)

        #END_CONSTRUCTOR
        pass

    def build_matrix(self, ctx, input):
        # ctx is the context object
        # return variables are: job_id
        #BEGIN build_matrix
        ''' Submit a job to build a distance matrix.

            @param input Dictionary of input variables (see spec file for valid keys)
            @return Job ID
        '''
        
        if 'file_paths' not in input:
            input['file_paths'] = list()
        job_id = start_job(self.config, ctx, input)
        ctx.log_info('Started job '+job_id+' to build a matrix')
        
        #END build_matrix

        # At some point might do deeper type checking...
        if not isinstance(job_id, basestring):
            raise ValueError('Method build_matrix return value ' +
                             'job_id is not type basestring as required.')
        # return the results
        return [job_id]
