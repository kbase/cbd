import sys
import unittest
import subprocess
import os
from biokbase.CompressionBasedDistance.Helpers import get_config

class TestUrlScript(unittest.TestCase):
    
    def setUp(self):
        self.cmd = os.path.join(os.environ["TARGET"], "bin/cbd-url")
        self.config = get_config(os.environ["KB_TEST_CONFIG"])
        
    def test_current(self):
        '''Run cbd-url and verify that the current url is returned.'''
        args = [ self.cmd ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 0)
        self.assertNotEqual(so.find("http://"), -1)
        self.assertEqual(se, '')
        lines = so.split("\n")
        self.url = lines[1]
       
    def test_help(self):
        '''Run cbd-url --help and verify that the major sections in the help text are present'''
        
        args = [ self.cmd, "--help" ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 0)
        self.assertNotEqual(so.find("NAME"), -1)
        self.assertNotEqual(so.find("SYNOPSIS"), -1)
        self.assertNotEqual(so.find("DESCRIPTION"), -1)
        self.assertNotEqual(so.find("EXAMPLES"), -1)
        self.assertEqual(se, '')
        
    def test_default(self):
        '''Run cbd-url default and verify that the default URL is returned.'''
        
        args = [ self.cmd, "default" ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 0)
        self.assertNotEqual(so.find("http://kbase.us/services/CompressionBasedDistance/"), -1)
        self.assertEqual(se, '')
        
    def test_seturl(self):
        '''Run cbd-url newurl and verify that the new URL is returned.'''
        
        args = [ self.cmd, self.config["cbd_url"] ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 0)
        lines = so.split("\n")
        self.assertEqual(lines[0], "New URL set to: " + self.config["cbd_url"])
        self.assertEqual(se, '')
        
    def test_badarg(self):
        '''Run cbd-url with a bad argument and verify that the error message is returned.'''
        
        args = [ self.cmd, "--chia" ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find("unrecognized arguments:"), -1)

if __name__ == '__main__':
    unittest.main()
