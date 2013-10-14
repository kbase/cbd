import sys
import unittest
import subprocess
import time
import os

class TestFilterMatrixScript(unittest.TestCase):
    '''
    Test inputs and option processing
    '''
        
    def setUp(self):
        self.cmd = os.path.join(os.environ['KB_TOP'], 'bin/cbd-filtermatrix')

    def tearDown(self):
        if os.path.exists('list.input'):
            os.remove('list.input')

    def test_help(self):
        '''Run cbd-filtermatrix --help and verify that the major sections in the help text are present'''
        
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
        '''Run cbd-filtermatrix with a bad option and verify that the error message is returned.'''
        
        args = [ self.cmd, 'input', 'source', 'dest', 'grouplist', '--chia' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('unrecognized arguments:'), -1)
        
    def test_missingOptionValue(self):
        '''Run cbd-filtermatrix with a missing option value and verify that the error message is returned.'''
        
        args = [ self.cmd, 'input', 'source', 'dest', 'grouplist', '--filter' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('expected one argument'), -1)
        
    def test_missingArg(self):
        '''Run cbd-filtermatrix with a missing argument and verify that the error message is returned.'''
        
        args = [ self.cmd,  'input', 'source', 'dest' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(so, '')
        self.assertNotEqual(se.find('too few arguments'), -1)

    def test_missingInputFile(self):
        '''Run cbd-filtermatrix with an invalid path to the input list file.'''

        args = [ self.cmd, 'badfile', 'source', 'dest', 'grouplist' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 1)
        self.assertNotEqual(so.find('No such file or directory'), -1)
        self.assertEqual(se, '')

    def test_missingGroupInputFile(self):
        '''Run cbd-filtermatrix with an input list file that has a missing group list.'''

        listf = open('list.input', 'w')
        listf.write('client-tests/1_V2.fasta\tday0\n')
        listf.write('client-tests/2_V2.fasta\n')
        listf.write('client-tests/3_V2.fasta\tday0\n')
        listf.close()

        args = [ self.cmd, 'list.input', 'source', 'dest', 'grouplist' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 1)
        self.assertNotEqual(so.find('Each line must contain a path and group list'), -1)
        self.assertEqual(se, '')
        
    def test_missingSourceFile(self):
        '''Run cbd-filtermatrix with an invalid path to the source distance matrix file.'''

        listf = open('list.input', 'w')
        listf.write('client-tests/1_V2.fasta\tday0\n')
        listf.write('client-tests/2_V2.fasta\tday0\n')
        listf.write('client-tests/3_V2.fasta\tday0\n')
        listf.write('client-tests/4_V2.fasta\tday0\n')
        listf.close()

        args = [ self.cmd, 'list.input', 'badfile', 'dest', 'grouplist' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 1)
        self.assertNotEqual(so.find('No such file or directory'), -1)
        self.assertEqual(se, '')
        
    def test_badFilterOptionValue(self):
        '''Run cbd-filtermatrix with an invalid --filter option value.'''

        listf = open('list.input', 'w')
        listf.write('client-tests/1_V2.fasta\tday0\n')
        listf.write('client-tests/2_V2.fasta\tday0\n')
        listf.write('client-tests/3_V2.fasta\tday0\n')
        listf.write('client-tests/4_V2.fasta\tday0\n')
        listf.close()

        args = [ self.cmd, 'list.input', 'client-tests/output.csv', 'dest.csv', 'day0', '--filter', 'chia' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 1)
        self.assertNotEqual(so.find("Filter 'chia' is not supported"), -1)
        self.assertEqual(se, '')
        
    def test_tooManyGroupsWithin(self):
        '''Run cbd-filtermatrix with an invalid --filter option value.'''

        listf = open('list.input', 'w')
        listf.write('client-tests/1_V2.fasta\tday0\n')
        listf.write('client-tests/2_V2.fasta\tday0\n')
        listf.write('client-tests/3_V2.fasta\tday0\n')
        listf.write('client-tests/4_V2.fasta\tday0\n')
        listf.close()

        args = [ self.cmd, 'list.input', 'client-tests/output.csv', 'dest.csv', 'day0;day1' ]
        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (so, se) = proc.communicate()
        self.assertEqual(proc.returncode, 1)
        self.assertNotEqual(so.find('Only one group can be specified with filter'), -1)
        self.assertEqual(se, '')
        
if __name__ == '__main__':
    unittest.main()
