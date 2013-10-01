import sys
import unittest
import subprocess
import time
import os
from biokbase.CompressionBasedDistance.Helpers import get_config

class TestBuildMatrixScript(unittest.TestCase):
    '''
    Test inputs and option processing
    '''
        
    def setUp(self):
        self.cmd = os.path.join(os.environ['KB_TOP'], 'bin/cbd-buildmatrix')
        self._config = get_config(os.environ["KB_TEST_CONFIG"])
        args = [ 'kbase-login', self._config['test_user'], '--password', self._config['test_pwd'] ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

    def tearDown(self):
        if os.path.exists('list.input'):
            os.remove('list.input')

    def test_help(self):
        '''Run cbd-buildmatrix --help and verify that the major sections in the help text are present'''
        
        args = [ self.cmd, '--help' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 0)
        self.assertNotEqual(so.find('NAME'), -1)
        self.assertNotEqual(so.find('SYNOPSIS'), -1)
        self.assertNotEqual(so.find('DESCRIPTION'), -1)
        self.assertNotEqual(so.find('EXAMPLES'), -1)
        self.assertEqual(se, '')
                
    def test_badOption(self):
        '''Run cbd-buildmatrix with a bad option and verify that the error message is returned.'''
        
        args = [ self.cmd, 'input', '--chia' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('unrecognized arguments:'), -1)
        
    def test_missingOptionValue(self):
        '''Run cbd-buildmatrix with a missing option value and verify that the error message is returned.'''
        
        args = [ self.cmd, 'input', '--format' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('expected one argument'), -1)
        
    def test_missingArg(self):
        '''Run cbd-buildmatrix with a missing argument and verify that the error message is returned.'''
        
        args = [ self.cmd, '--format', 'fasta' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('too few arguments'), -1)

    def test_missingInputFile(self):
        '''Run cbd-buildmatrix with an invalid path to the input list file.'''

        args = [ self.cmd, 'badfile' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 1)
        self.assertNotEqual(so.find('No such file or directory'), -1)
        self.assertEqual(se, '')

    def test_badInputFile(self):
        '''Run cbd-buildmatrix with an input list file that has a bad path to a sequence file.'''

        listf = open('list.input', 'w')
        listf.write('client-tests/1_V2.fasta\n')
        listf.write('badfile\n')
        listf.write('client-tests/3_V2.fasta\n')
        listf.close()

        args = [ self.cmd, 'list.input' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 1)
        self.assertNotEqual(so.find('1 files are not accessible'), -1)
        self.assertEqual(se, '')

if __name__ == '__main__':
    unittest.main()
