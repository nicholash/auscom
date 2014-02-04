
import unittest
import subprocess

class TestBasic(unittest.TestCase):

    def test_build(self):
        """
        Build all auscom models. 
        """
        
        ret = subprocess.call(['../bin/clean_auscom.sh', 'nci'], shell=True)
        self.assertEqual(ret, 0)
        ret = subprocess.call(['../bin/build_auscom.sh', 'nci'], shell=True)
        self.assertEqual(ret, 0)

    def test_run(self):
        """
        Do a one month low res run and check for successful completion. 
        """

        ret = subprocess.call(['../bin/run.py', '--newrun', '--rundirect', '--submitruntime', '1', 'cnyf2.mom5'])
        self.assertEqual(ret, 0)

if __name__ == '__main__':
    unittest.main()
