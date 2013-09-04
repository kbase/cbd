import unittest
import sys
import os
from biokbase.CompressionBasedDistance.Client import CompressionBasedDistance
from biokbase.CompressionBasedDistance.Helpers import get_config
from biokbase.CompressionBasedDistance.Shock import Client as ShockClient

InputFiles = [ 'client-tests/1_V2.fasta', 'client-tests/2_V2.fasta', 'client-tests/3_V2.fasta', 'client-tests/4_V2.fasta' ]

class TestPythonClient(unittest.TestCase):    

    def setUp(self):
        # Set configuration variables.
        self._config = get_config(os.environ["KB_TEST_CONFIG"])

    def test_buildmatrix(self):
        ''' Run buildmatrix() with four simple sequence files and verify the returned distance matrix.'''

        # Create a client.
        cbdClient = CompressionBasedDistance(self._config["cbd_url"], user_id=self._config["test_user"], password=self._config["test_pwd"])
        token = cbdClient._headers['AUTHORIZATION']
        
        # Create the input parameters.
        input = dict()
        input['auth'] = token
        input['format'] = 'fasta'
        input['scale'] = 'std'
        input['node_ids'] = list()

        # Upload the files to Shock.
        shockClient = ShockClient(self._config['shock_url'], token)
        for filename in InputFiles:
            node = shockClient.create_node(filename, '')
            input['node_ids'].append(node['id'])
        
        # Run the buildmatrix() function to generate a distance matrix.
        output = cbdClient.build_matrix(input)
        
        # Confirm the returned distance matrix matches the saved valid output.
        vf = open('client-tests/output.csv', 'r')
        for index in range(0,len(output)):
            line = vf.readline()
            self.assertEqual(line, output[index])
        self.assertEqual(vf.readline(), '')
        vf.close()
        
if __name__ == '__main__':
    # Create a suite, add tests to the suite, run the suite.
    suite = unittest.TestSuite()
    suite.addTest(TestPythonClient('test_buildmatrix'))
    unittest.TextTestRunner().run(suite)
    