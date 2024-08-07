from tests import SysdiagnoseTestCase
import unittest
import glob
import os
import importlib.util
import sysdiagnose

'''
Test file structure of parsers
'''


class TestParsers(SysdiagnoseTestCase):

    def list_all_parsers(self):
        sd = sysdiagnose.Sysdiagnose()
        modules = glob.glob(os.path.join(sd.parsers_folder, "*.py"))
        for parser in modules:
            if parser.endswith('__init__.py'):
                continue
            yield parser

    def test_parsers_filestructure(self):
        required_functions = ['get_log_files', 'parse_path']  # TODO add parse_path_to_folder(path: str, output_folder: str) -> bool:
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
