import unittest
import sys
import os
import time
import subprocess
from biokbase.CompressionBasedDistance.Client import CompressionBasedDistance
from biokbase.CompressionBasedDistance.Helpers import get_config
from biokbase.CompressionBasedDistance.Shock import Client as ShockClient

InputFiles = [ 'client-tests/1_V2.fasta', 'client-tests/2_V2.fasta', 'client-tests/3_V2.fasta', 'client-tests/4_V2.fasta' ]

class TestPythonClient(unittest.TestCase):    

    def setUp(self):
        # Set configuration variables.
        self._config = get_config(os.environ["KB_TEST_CONFIG"])

    def test_buildmatrix(self):
        ''' Run build_matrix() with four simple sequence files and verify the returned distance matrix.'''

        # Create a client.
        cbdClient = CompressionBasedDistance(self._config["cbd_url"], user_id=self._config["test_user"], password=self._config["test_pwd"])
        token = cbdClient._headers['AUTHORIZATION']
        
        # Create the input parameters.
        input = dict()
        input['format'] = 'fasta'
        input['scale'] = 'std'
        input['node_ids'] = list()

        # Upload the files to Shock.
        shockClient = ShockClient(self._config['shock_url'], token)
        for filename in InputFiles:
            node = shockClient.create_node(filename, '')
            input['node_ids'].append(node['id'])
        
        # Run the buildmatrix() function to generate a distance matrix.
        jobid = cbdClient.build_matrix(input)

        # Wait for the distance matrix to be built.
        time.sleep(30)

        # Get the distance matrix and save to a file.
        outputPath = 'client-tests/unittest.csv'
        args = [ os.path.join(os.environ['KB_TOP'], 'bin/cbd-getmatrix'), jobid,  outputPath ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 0)
        
        # Confirm the returned distance matrix matches the saved valid output.
        vf = open('client-tests/output.csv', 'r')
        tf = open(outputPath, 'r')
        for vline in vf: 
            tline = tf.readline()
            self.assertEqual(vline, tline)
        self.assertEqual(tf.readline(), '')
        vf.close()
        tf.close()
        os.remove(outputPath)
        
if __name__ == '__main__':
    # Create a suite, add tests to the suite, run the suite.
    suite = unittest.TestSuite()
    suite.addTest(TestPythonClient('test_buildmatrix'))
    unittest.TextTestRunner().run(suite)
    
