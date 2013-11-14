import sys
import unittest
import subprocess
import time
import os

class TestPlotMatrixScript(unittest.TestCase):
    '''
    Test inputs and option processing
    '''
        
    def setUp(self):
        self.cmd = os.path.join(os.environ['KB_TOP'], 'bin/cbd-plotmatrix')

    def tearDown(self):
        if os.path.exists('list.input'):
            os.remove('list.input')

    def test_help(self):
        '''Run cbd-plotmatrix --help and verify that the major sections in the help text are present'''
        
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
        '''Run cbd-plotmatrix with a bad option and verify that the error message is returned.'''
        
        args = [ self.cmd, 'source', 'dest', '--chia' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('unrecognized arguments:'), -1)
        
    def test_missingOptionValue(self):
        '''Run cbd-plotmatrix with a missing option value and verify that the error message is returned.'''
        
        args = [ self.cmd, 'source', 'dest', '--type' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('expected one argument'), -1)
        
    def test_missingArg(self):
        '''Run cbd-plotmatrix with a missing argument and verify that the error message is returned.'''
        
        args = [ self.cmd, 'source' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('too few arguments'), -1)

    def test_missingSourceFile(self):
        '''Run cbd-plotmatrix with an invalid path to the input list file.'''

        args = [ self.cmd, 'badfile', 'dest' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 1)
        self.assertNotEqual(so.find('No such file or directory'), -1)
        self.assertEqual(se, '')

if __name__ == '__main__':
    unittest.main()
