from tests import SysdiagnoseTestCase
import unittest
import importlib.util
from sysdiagnose.utils.base import BaseParserInterface

'''
Test file structure of parsers
'''


class TestParsers(SysdiagnoseTestCase):

    def test_parsers_filestructure(self):
        required_functions = ['execute']
        required_variables = ['description']

        print("Checking parsers for required functions and variables...")
        for parser_name in self.get_parsers():
            print(f"- {parser_name}")

            module = importlib.import_module(f'sysdiagnose.parsers.{parser_name}')
            # spec = importlib.util.spec_from_file_location(parser_fname[:-3], parser)
            # module = importlib.util.module_from_spec(spec)
            # spec.loader.exec_module(module)

            # figure out the class name
            obj = None
            obj_instance = None
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, BaseParserInterface) and obj is not BaseParserInterface:
                    obj_instance: BaseParserInterface = obj(config=self.sd.config, case_id='1')
                    break

            self.assertIsNotNone(obj_instance, f'Parser {parser_name} is missing a class definition inheriting BaseParserInterface.')
            # ensure the module_filename is correct, and not from a parent class
            self.assertEqual(obj_instance.module_name, parser_name, f'Parser {parser_name} has incorrect module_filename. Did you add the following?\n    def __init__(self, config: dict, case_id: str):\n        super().__init__(__file__, config, case_id)')

            # check for required functions and variables
            for required_function in required_functions:
                self.assertTrue(hasattr(obj, required_function), f'Parser {parser_name} is missing {required_function} function.')
            for required_variable in required_variables:
                self.assertTrue(hasattr(obj, required_variable), f'Parser {parser_name} is missing {required_variable} variable.')


if __name__ == '__main__':
    unittest.main()
