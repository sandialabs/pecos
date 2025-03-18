# This is a test to ensure all of the examples run.
import os
import sys
import unittest
import pytest
from os.path import abspath, dirname, join, basename
from subprocess import call
from glob import glob

testdir = dirname(abspath(str(__file__)))
examplesdir = join(testdir, "..", "..", "examples")


class TestExamples(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        import pecos

        self.pecos = pecos

    @classmethod
    def tearDownClass(self):
        pass
    
    @pytest.mark.time_consuming
    def test_that_examples_run(self):
        cwd = os.getcwd()
        example_files = []
        failed_examples = []
        flag = 0
        for f in glob(join(examplesdir, '**', '*.py'), recursive=True):
            filename = basename(f)
            directory = dirname(f)
            example_files.append(filename)
            os.chdir(directory)
            tmp_flag = call([sys.executable, filename])
            print(filename, tmp_flag)
            if tmp_flag == 1:
                failed_examples.append(filename)
                flag = 1
        os.chdir(cwd)
        if len(failed_examples) > 0:
            print("failed examples: {0}".format(failed_examples))
        self.assertEqual(flag, 0)


if __name__ == "__main__":
    unittest.main()
