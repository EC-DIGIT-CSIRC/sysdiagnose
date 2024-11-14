from tests import SysdiagnoseTestCase
import unittest
import importlib.util
from sysdiagnose.utils.base import BaseParserInterface
import os

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

    def test_parsers_no_parser_yet(self):
        print("Checking for files that are not yet parsed...")

        # get covered files and folders
        covered_files_and_folders = []
        all_files_and_folders = []

        for case_id in self.sd.get_case_ids():
            obj_instance = None
            for parser_name in self.get_parsers():
                module = importlib.import_module(f'sysdiagnose.parsers.{parser_name}')
                # figure out the class name
                obj = None
                obj_instance = None
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if isinstance(obj, type) and issubclass(obj, BaseParserInterface) and obj is not BaseParserInterface:
                        obj_instance: BaseParserInterface = obj(config=self.sd.config, case_id=case_id)

                        module_files_and_folders = obj_instance.get_log_files()
                        covered_files_and_folders.extend(module_files_and_folders)

                        break
            if obj_instance:
                # get all files and folders
                for root, dirs, files in os.walk(obj_instance.case_data_folder):
                    for file in files:
                        all_files_and_folders.append(os.path.join(root, file))

        # get difference
        not_covered = []
        for file in all_files_and_folders:
            # skip files that start with a .
            if os.path.basename(file).startswith('.'):
                continue

            covered = False
            for covered_file in covered_files_and_folders:
                if file.startswith(covered_file):
                    covered = True
                    break

            if not covered and os.path.getsize(file) > 10:
                not_covered.append(file)
                print(f"File not yet parsed: {file}")

        # sort by the last part of the path (excluding the first 6 folders in the path)
        not_covered = sorted(not_covered, key=lambda x: '/'.join(x.split('/')[7:]))

        with open('not_yet_parsed.txt', 'w') as f:
            f.write('\n'.join(not_covered))
        pass


if __name__ == '__main__':
    unittest.main()
