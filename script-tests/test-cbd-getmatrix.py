import sys
import unittest
import subprocess
import time
import os

class TestGetMatrixScript(unittest.TestCase):
    '''
    Test inputs and option processing
    '''
        
    def setUp(self):
        self.cmd = os.path.join(os.environ['TARGET'], 'bin/cbd-getmatrix')

    def test_help(self):
        '''Run cbd-getmatrix --help and verify that the major sections in the help text are present'''
        
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
        '''Run cbd-getmatrix with a bad option and verify that the error message is returned.'''
        
        args = [ self.cmd, 'job', 'output', '--chia' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('unrecognized arguments:'), -1)
        
    def test_missingOptionValue(self):
        '''Run cbd-getmatrix with a missing option value and verify that the error message is returned.'''
        
        args = [ self.cmd, 'job', 'output', '--shock-url' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('expected one argument'), -1)
        
    def test_missingArg(self):
        '''Run cbd-getmatrix with a missing argument and verify that the error message is returned.'''
        
        args = [ self.cmd, 'job', '--shock-url', 'http://localhost:7000' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('too few arguments'), -1)

        # Test a bad jobid 
        
if __name__ == '__main__':
    unittest.main()
