from tests import SysdiagnoseTestCase
import unittest
import importlib.util
from sysdiagnose.utils.base import BaseAnalyserInterface

'''
Test file structure of analysers
'''


class TestAnalysers(SysdiagnoseTestCase):

    def test_analysers_filestructure(self):
        required_functions = ['execute']
        required_variables = ['description']

        print("Checking analysers for required functions and variables...")
        for name in self.get_analysers():
            print(f"- {name}")

            module = importlib.import_module(f'sysdiagnose.analysers.{name}')

            # figure out the class name
            obj = None
            obj_instance = None
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, BaseAnalyserInterface) and obj is not BaseAnalyserInterface:
                    obj_instance: BaseAnalyserInterface = obj(config=self.sd.config, case_id='1')
                    break

            self.assertIsNotNone(obj_instance, f'Analyser {name} is missing a class definition inheriting BaseAnalyserInterface.')
            # ensure the module_filename is correct, and not from a parent class
            self.assertEqual(obj_instance.module_name, name, f'Analyser {name} has incorrect module_filename. Did you add the following?\n    def __init__(self, config: dict, case_id: str):\n        super().__init__(__file__, config, case_id)')

            # check for required functions and variables
            for required_function in required_functions:
                self.assertTrue(hasattr(obj, required_function), f'Analyser {name} is missing {required_function} function.')
            for required_variable in required_variables:
                self.assertTrue(hasattr(obj, required_variable), f'Analyser {name} is missing {required_variable} variable.')


if __name__ == '__main__':
    unittest.main()
