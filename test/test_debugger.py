import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import unittest
import glob
import subprocess


from back.debugger import Debugger

class TestDebugger(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.c_files = glob.glob("*.c")
        cls.binary_files = []
        for c_file in cls.c_files:
            output_name = os.path.splitext(c_file)[0]
            subprocess.run(["gcc", c_file, "-o", output_name],
               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cls.binary_files.append(output_name)

    def test_parse_code2(self):
        debugger = Debugger(self.c_files[1], self.binary_files[1])
        functions = debugger.parse_code()
        self.assertEqual(functions, {"main": (20, 46), "greet": (49, 52)
                                     , "add": (55, 60), "printArray": (63, 71)})

