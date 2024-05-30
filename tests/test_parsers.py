from tests import SysdiagnoseTestCase
import unittest
import glob
import os
import importlib.util

'''
Test file structure of parsers
'''


class TestParsers(SysdiagnoseTestCase):

    def list_all_parsers(self):
        parsers_folder = 'parsers'
        modules = glob.glob(os.path.join(parsers_folder, "*.py"))
        for parser in modules:
            if parser.endswith('__init__.py') or parser.endswith('demo_parser.py'):
                continue
            yield parser

    def test_parsers_filestructure(self):
        required_functions = ['get_log_files', 'parse_path']
        required_variables = ['parser_description']

        parsers = self.list_all_parsers()
        for parser in parsers:
            parser_fname = os.path.basename(parser)
            spec = importlib.util.spec_from_file_location(parser_fname[:-3], parser)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for required_function in required_functions:
                self.assertTrue(hasattr(module, required_function), f'Parser {parser_fname} is missing {required_function} function.')
            for required_variable in required_variables:
                self.assertTrue(hasattr(module, required_variable), f'Parser {parser_fname} is missing {required_variable} variable.')
            print(parser)
        pass


if __name__ == '__main__':
    unittest.main()
