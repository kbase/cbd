import sys
import unittest
import subprocess
import time
import os

class TestBuildMatrixScript(unittest.TestCase):
    '''
    Test inputs and option processing
    '''
        
    def setUp(self):
        self.cmd = os.path.join(os.environ["TARGET"], "bin/cbd-buildmatrix")

    def test_help(self):
        '''Run cbd-buildmatrix --help and verify that the major sections in the help text are present'''
        
        args = [ self.cmd, "--help" ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 0)
        self.assertNotEqual(so.find("NAME"), -1)
        self.assertNotEqual(so.find("SYNOPSIS"), -1)
        self.assertNotEqual(so.find("DESCRIPTION"), -1)
        self.assertNotEqual(so.find("EXAMPLES"), -1)
        self.assertEqual(se, '')
                
    def test_badOption(self):
        '''Run cbd-buildmatrix with a bad option and verify that the error message is returned.'''
        
        args = [ self.cmd, "input", "output", "--chia" ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find("unrecognized arguments:"), -1)
        
    def test_missingOptionValue(self):
        '''Run cbd-buildmatrix with a missing option value and verify that the error message is returned.'''
        
        args = [ self.cmd, "input", "output", "--format" ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find("expected one argument"), -1)
        
    def test_missingArg(self):
        '''Run cbd-buildmatrix with a missing argument and verify that the error message is returned.'''
        
        args = [ self.cmd, "input", "--format", "fasta" ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find("too few arguments"), -1)

if __name__ == '__main__':
    # Since I can't get this from python I think...
    unittest.main()
