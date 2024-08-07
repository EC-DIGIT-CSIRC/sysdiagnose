#!/usr/bin/env python

from tabulate import tabulate
import argparse
import glob
import hashlib
import importlib.util
import json
import os
import re
import sys
import tarfile


def main():
    parser = argparse.ArgumentParser(
        prog='sysdiagnose',
        description='sysdiagnose parsing and analysis'
    )
    # available for all
    parser.add_argument('-c', '--case_id', required=False, default='all', help='ID of the case, or "all" for all cases (default)')

    subparsers = parser.add_subparsers(dest='mode')

    # init mode
    init_parser = subparsers.add_parser('init', help='Initialize a new case')
    init_parser.add_argument('filename', help='Name of the sysdiagnose archive file')
    init_parser.add_argument('--force', action='store_true', help='Force case creation')

    # parse mode
    parse_parser = subparsers.add_parser('parse', help='Parse a case')
    parse_parser.add_argument('parser', help='Name of the parser, "all" for running all parsers, or "list" for a listing of all parsers')
    parse_parser.error = parse_parser_error

    # analyse mode
    analyse_parser = subparsers.add_parser('analyse', help='Analyse a case')
    analyse_parser.add_argument('analyser', help='Name of the analyser, "all" for running all analysers, or "list" for a listing of all analysers')
    analyse_parser.error = analyse_parser_error

    # list mode
    list_parser = subparsers.add_parser('list', help='List ...')
    list_parser.add_argument('what', choices=['cases', 'parsers', 'analysers'], help='List cases, parsers or analysers')

    parser.parse_args()

    args = parser.parse_args()

    sd = Sysdiagnose()

    if args.mode == 'list':
        if args.what == 'cases':
            sd.print_list_cases()
        elif args.what == 'parsers':
            sd.print_parsers_list()
        elif args.what == 'analysers':
            sd.print_analysers_list()

    elif args.mode == 'init':
        # Handle init mode
        filename = args.filename
        force = args.force

        if not os.path.isfile(filename) and filename.endswith('.tar.gz'):
            exit(f"File {filename} does not exist or is not a tar.gz file")
        # create the case
        try:
            if args.case_id and args.case_id != 'all':
                case_id = args.case_id
                sd.create_case(filename, force, case_id)
            else:
                case_id = sd.create_case(filename, force)
        except Exception as e:
            exit(f"Error creating case: {str(e)}")

    elif args.mode == 'parse':
        # Handle parse mode
        if args.parser == 'list':
            sd.print_parsers_list()
            return
        elif args.parser == 'all':
            parsers = list(sd.get_parsers().keys())
        elif not sd.is_valid_parser_name(args.parser):
            sd.print_parsers_list()
            print("")
            exit(f"Parser '{args.parser}' does not exist, possible options are listed above.")
        else:
            parsers = [args.parser]

        if args.case_id == 'all':
            case_ids = sd.get_case_ids()
        elif not sd.is_valid_case_id(args.case_id):
            sd.print_list_cases()
            print("")
            exit(f"Case ID '{args.case_id}' does not exist, possible options are listed above.")
        else:
            case_ids = [args.case_id]

        for case_id in case_ids:
            print(f"Case ID: {case_id}")
            for parser in parsers:
                print(f"Parser '{parser}' for case ID '{case_id}'")
                try:
                    sd.parse(parser, case_id)
                except NotImplementedError:
                    print(f"Parser '{parser}' is not implemented yet, skipping")

    elif args.mode == 'analyse':
        # Handle analyse mode
        if args.analyser == 'list':
            sd.print_analysers_list()
            return
        elif args.analyser == 'all':
            analysers = list(sd.get_analysers().keys())
        elif not sd.is_valid_analyser_name(args.analyser):
            sd.print_analysers_list()
            print("")
            exit(f"Analyser '{args.analyser}' does not exist, possible options are listed above.")
        else:
            analysers = [args.analyser]

        if args.case_id == 'all':
            case_ids = sd.get_case_ids()
        elif not sd.is_valid_case_id(args.case_id):
            sd.print_list_cases()
            print("")
            exit(f"Case ID '{args.case_id}' does not exist, possible options are listed above.")
        else:
            case_ids = [args.case_id]

        for case_id in case_ids:
            print(f"Case ID: {case_id}")
            for analyser in analysers:
                print(f"  Analyser '{analyser}' for case ID '{case_id}'")
                try:
                    sd.analyse(analyser, case_id)
                except NotImplementedError:
                    print(f"Analyser '{analyser}' is not implemented yet, skipping")
    else:
        parser.print_help()


def parse_parser_error(message):
    sd = Sysdiagnose()
    print(message, file=sys.stderr)
    print("Available parsers:")
    print("")
    sd.print_parsers_list()
    sys.exit(2)


def analyse_parser_error(message):
    sd = Sysdiagnose()
    print(message, file=sys.stderr)
    print("Available analysers:")
    print("")
    sd.print_analysers_list()
    sys.exit(2)


class Sysdiagnose:
    def __init__(self):
        self.config_folder = os.path.dirname(os.path.abspath(__file__))
        self.parsers_folder = os.path.join(self.config_folder, "parsers")
        self.analysers_folder = os.path.join(self.config_folder, "analysers")

        # case data is in current working directory by default
        self.cases_root_folder = os.getenv('SYSDIAGNOSE_CASES_PATH', '.')

        self.cases_file = os.path.join(self.cases_root_folder, "cases.json")
        self.data_folder = os.path.join(self.cases_root_folder, "data")
        self.parsed_data_folder = os.path.join(self.cases_root_folder, "parsed_data")  # stay in current folder

        self._cases = False

        os.makedirs(self.cases_root_folder, exist_ok=True)
        os.makedirs(self.data_folder, exist_ok=True)
        os.makedirs(self.parsed_data_folder, exist_ok=True)

    def cases(self):
        # singleton, so it's not loaded unless necessary
        # load cases + migration of old cases format to new format
        if not self._cases:
            try:
                with open(self.cases_file, 'r') as f:
                    self._cases = json.load(f)
                    if 'cases' in self._cases:  # conversion is needed
                        new_format = {}
                        for case in self._cases['cases']:
                            case['case_id'] = str(case['case_id'])
                            new_format[case['case_id']] = case

                        cases = new_format
                        with open(self.cases_file, 'w') as f:
                            json.dump(cases, f, indent=4)
            except FileNotFoundError:
                self._cases = {}
        return self._cases

    def create_case(self, sysdiagnose_file: str, force: bool = False, case_id: bool | str = False) -> int:
        '''
        Extracts the sysdiagnose file and creates a new case.

        Parameters:
            sysdiagnose_file (str): Path to the sysdiagnose file.
            force (bool): Whether to force the creation of a new case.
            case_id (str): The case ID to use, or False to generate a new incremental one.

        Returns:
            int: The case ID of the new case.
        '''
        from parsers import remotectl_dumpstate

        # test sysdiagnose file
        try:
            tf = tarfile.open(sysdiagnose_file)
        except Exception as e:
            raise FileNotFoundError(f'Error opening sysdiagnose file. Reason: {str(e)}')

        # calculate sha256 of sysdiagnose file and compare with past cases
        try:
            with open(sysdiagnose_file, 'rb') as f:
                bytes = f.read()  # read entire file as bytes
                readable_hash = hashlib.sha256(bytes).hexdigest()
        except Exception as e:
            raise Exception(f'Error calculating sha256. Reason: {str(e)}')

        # only allow specific chars for case_id
        if case_id:
            if not re.match(r'^[a-zA-Z0-9-_]+$', case_id):
                raise ValueError("Invalid case ID. Only alphanumeric and -_ characters are allowed.")

        # check if sysdiagnise file is already in a case
        case = None
        for c in self.cases().values():
            if c['source_sha256'] == readable_hash:
                if force:
                    if case_id and c['case_id'] != case_id:
                        raise ValueError(f"This sysdiagnose has already been extracted + incoherent caseID: existing = {c['case_id']}, given = {case_id}")
                    # all is well
                    case_id = c['case_id']
                    case = c
                    break
                else:
                    raise ValueError(f"This sysdiagnose has already been extracted for case ID: {c['case_id']}")

        # incoherent caseID and file
        if case_id and case_id in self.cases():
            if self.cases()[case_id]['source_sha256'] != readable_hash:
                raise ValueError(f"Case ID {case_id} already exists but with a different sysdiagnose file.")

        # find next incremental case_id, if needed
        if not case_id:
            case_id = 0
            for k in self.cases().keys():
                try:
                    case_id = max(case_id, int(k))
                except ValueError:
                    pass
            # add one to the new found case_id
            case_id += 1
            case_id = str(case_id)

        if not case:
            # if sysdiagnose file is new and legit, create new case and extract files
            case = {
                'case_id': case_id,
                'source_file': sysdiagnose_file,
                'source_sha256': readable_hash,
                'serial_number': "<unknown>",
                'unique_device_id': "<unknown>"
            }

        # create case folder
        case_folder = os.path.join(self.data_folder, str(case['case_id']))
        os.makedirs(case_folder, exist_ok=True)

        # create parsed_data folder
        parsed_folder = os.path.join(self.parsed_data_folder, str(case['case_id']))
        os.makedirs(parsed_folder, exist_ok=True)

        # extract sysdiagnose files
        try:
            tf.extractall(path=case_folder)
        except Exception as e:
            raise Exception(f'Error while decompressing sysdiagnose file. Reason: {str(e)}')

        # create case json file
        new_case_json = {
            "sysdiagnose.log": glob.glob(os.path.join(case_folder, '*', 'sysdiagnose.log'))[0],
        }

        # ips files
        try:
            new_case_json["ips_files"] = glob.glob(os.path.join(case_folder, '*', 'crashes_and_spins', '*.ips'))
        except:        # noqa: E722
            pass

        # Get iOS version
        version = '<unknown>'
        try:
            with open(new_case_json['sysdiagnose.log'], 'r') as f:
                line_version = [line for line in f if 'iPhone OS' in line][0]
                version = line_version.split()[4]
            new_case_json['ios_version'] = version
            case['ios_version'] = version
        except Exception as e:
            raise Exception(f"Could not open file {new_case_json['sysdiagnose.log']}. Reason: {str(e)}")

        # Save JSON file
        case_fname = os.path.join(self.data_folder, f"{case_id}.json")
        with open(case_fname, 'w') as data_file:
            data_file.write(json.dumps(new_case_json, indent=4))

        # update cases list file
        extracted_files_path = os.path.join(case_folder, os.listdir(case_folder).pop())
        remotectl_dumpstate_json = remotectl_dumpstate.parse_path(extracted_files_path)
        try:
            case['serial_number'] = remotectl_dumpstate_json['Local device']['Properties']['SerialNumber']
            case['unique_device_id'] = remotectl_dumpstate_json['Local device']['Properties']['UniqueDeviceID']
        except KeyError as e:
            print(f"WARNING: Could not parse remotectl_dumpstate, and therefore extract serial numbers. Error {e}")

        # update case if needed
        self.cases()[case['case_id']] = case

        # FIXME implement file locking mechanism for concurrent access
        with open(self.cases_file, 'w') as f:
            json.dump(self.cases(), f, indent=4)

        print("Sysdiagnose file has been processed")
        print(f"Case ID: {str(case['case_id'])}")
        return case['case_id']

    def parse(self, parser: str, case_id: str):
        # Load parser module
        spec = importlib.util.spec_from_file_location(parser, os.path.join(self.parsers_folder, parser) + '.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        case_folder = os.path.join(self.data_folder, case_id)
        if not os.path.isdir(case_folder):
            print(f"Case {case_id} does not exist", file=sys.stderr)
            return -1

        extracted_files_path = os.path.join(case_folder, os.listdir(case_folder).pop())

        if hasattr(module, 'parse_path_to_folder'):
            output_folder = os.path.join(self.parsed_data_folder, case_id)
            os.makedirs(output_folder, exist_ok=True)
            result = module.parse_path_to_folder(path=extracted_files_path, output_folder=output_folder)
            print(f'Execution finished, output saved in: {output_folder}', file=sys.stderr)
        else:  # if the module cannot (yet) save directly to a folder, we wrap around by doing it ourselves
            # parsers that output in the result variable
            # building command
            result = module.parse_path(path=extracted_files_path)
            # saving the parser output
            output_file = os.path.join(self.parsed_data_folder, case_id, f"{parser}.json")
            with open(output_file, 'w') as data_file:
                data_file.write(json.dumps(result, indent=4, ensure_ascii=False))
            print(f'Execution finished, output saved in: {output_file}', file=sys.stderr)
        return 0

    def analyse(self, analyser: str, case_id: str):
        # Load parser module
        spec = importlib.util.spec_from_file_location(analyser, os.path.join(self.analysers_folder, analyser + '.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # building command
        parse_data_path = os.path.join(self.parsed_data_folder, case_id)
        if not os.path.isdir(parse_data_path):
            print(f"Case {case_id} does not exist", file=sys.stderr)
            return -1
        output_file = os.path.join(self.parsed_data_folder, case_id, analyser + "." + module.analyser_format)
        module.analyse_path(case_folder=parse_data_path, output_file=output_file)
        print(f'Execution success, output saved in: {output_file}', file=sys.stderr)

        return 0

    def print_list_cases(self):
        print("#### case List ####")
        headers = ['Case ID', 'Source file', 'serial number']
        lines = []
        for case in self.cases().values():
            line = [case['case_id'], case['source_file'], case.get('serial_number', '<unknown>')]
            lines.append(line)

        print(tabulate(lines, headers=headers))

    def get_case_ids(self):
        case_ids = list(self.cases().keys())
        case_ids.sort()
        return case_ids

    def is_valid_case_id(self, case_id):
        return case_id in self.cases()

    def is_valid_parser_name(self, name):
        if name == '__init__':
            return False
        fname = os.path.join(self.parsers_folder, f'{name}.py')
        if os.path.isfile(fname):
            try:
                spec = importlib.util.spec_from_file_location(name, fname)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return True
            except AttributeError:
                return False
        return False

    def is_valid_analyser_name(self, name):
        if name == '__init__':
            return False
        fname = os.path.join(self.analysers_folder, f'{name}.py')
        if os.path.isfile(fname):
            try:
                spec = importlib.util.spec_from_file_location(name, fname)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return True
            except AttributeError:
                return False
        return False

    def get_parsers(self) -> dict:
        modules = glob.glob(os.path.join(self.parsers_folder, '*.py'))
        parsers = {}
        for parser in modules:
            if parser.endswith('__init__.py'):
                continue
            try:
                name = parser[len(self.parsers_folder) + 1:-3]
                spec = importlib.util.spec_from_file_location(name, parser)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                parsers[name] = module.parser_description
            except AttributeError:
                continue
        parsers = dict(sorted(parsers.items()))
        return parsers

    def get_analysers(self) -> dict:
        modules = glob.glob(os.path.join(self.analysers_folder, '*.py'))
        analysers = {}
        for parser in modules:
            if parser.endswith('__init__.py'):
                continue
            try:
                name = parser[len(self.analysers_folder) + 1:-3]
                spec = importlib.util.spec_from_file_location(name, parser)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                analysers[name] = module.analyser_description
            except AttributeError:
                continue
        analysers = dict(sorted(analysers.items()))
        return analysers

    def print_parsers_list(self) -> None:
        lines = [['all', 'Run all parsers']]
        for parser, description in self.get_parsers().items():
            lines.append([parser, description])

        headers = ['Parser Name', 'Parser Description']
        print(tabulate(lines, headers=headers))

    def print_analysers_list(self):
        lines = [['all', 'Run all analysers']]
        for analyser, description in self.get_analysers().items():
            lines.append([analyser, description])

        headers = ['Analyser Name', 'Analyser Description']
        print(tabulate(lines, headers=headers))


if __name__ == "__main__":
    main()
