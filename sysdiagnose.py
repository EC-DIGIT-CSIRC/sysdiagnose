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
import fcntl
from utils.base import BaseParserInterface, BaseAnalyserInterface, SysdiagnoseConfig


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

    # just for convenience
    subparsers.add_parser('cases', help='List cases')
    subparsers.add_parser('parsers', help='List parsers')
    subparsers.add_parser('analysers', help='List analysers')

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

    elif args.mode == 'cases':
        sd.print_list_cases()

    elif args.mode == 'parsers':
        sd.print_parsers_list()

    elif args.mode == 'analysers':
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
            parsers_list = list(sd.get_parsers().keys())
        elif not sd.is_valid_parser_name(args.parser):
            sd.print_parsers_list()
            print("")
            exit(f"Parser '{args.parser}' does not exist, possible options are listed above.")
        else:
            parsers_list = [args.parser]

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
            for parser in parsers_list:
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
            analysers_list = list(sd.get_analysers().keys())
        elif not sd.is_valid_analyser_name(args.analyser):
            sd.print_analysers_list()
            print("")
            exit(f"Analyser '{args.analyser}' does not exist, possible options are listed above.")
        else:
            analysers_list = [args.analyser]

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
            for analyser in analysers_list:
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
    def __init__(self, cases_path=os.getenv('SYSDIAGNOSE_CASES_PATH', './cases')):
        self._cases = False   # will be populated through cases() singleton method
        self.config = SysdiagnoseConfig(cases_path)

    def cases(self, force: bool = False) -> dict:
        # pseudo singleton, so it's not loaded unless necessary
        # load cases + migration of old cases format to new format
        if not self._cases or force:
            try:
                with open(self.config.cases_file, 'r+') as f:
                    try:
                        fcntl.flock(f, fcntl.LOCK_EX)        # enable lock
                        self._cases = json.load(f)
                        if 'cases' in self._cases:  # conversion is needed
                            new_format = {}
                            for case in self._cases['cases']:
                                case['case_id'] = str(case['case_id'])
                                new_format[case['case_id']] = case

                            cases = new_format
                            f.seek(0)
                            json.dump(cases, f, indent=4)
                            f.truncate()
                    finally:
                        fcntl.flock(f, fcntl.LOCK_UN)
            except FileNotFoundError:
                self._cases = {}
                with open(self.config.cases_file, 'w') as f:
                    try:
                        fcntl.flock(f, fcntl.LOCK_EX)        # enable lock
                        json.dump(self._cases, f, indent=4)
                    finally:
                        fcntl.flock(f, fcntl.LOCK_UN)

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
                'date': "<unknown>",  # date when sysdiagnose was taken
                'case_id': case_id,
                'source_file': sysdiagnose_file,
                'source_sha256': readable_hash,
                'serial_number': "<unknown>",
                'unique_device_id': "<unknown>"
            }

        # create case folder
        case_folder = os.path.join(self.config.data_folder, str(case['case_id']))
        os.makedirs(case_folder, exist_ok=True)

        # create parsed_data folder
        parsed_folder = os.path.join(self.config.parsed_data_folder, str(case['case_id']))
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
                case['date'] = f.readline().split(': ')[0]  # we don't know the timezone !!!
                line_version = [line for line in f if 'iPhone OS' in line][0]
                version = line_version.split()[4]
            new_case_json['ios_version'] = version
            case['ios_version'] = version
        except Exception as e:
            raise Exception(f"Could not open file {new_case_json['sysdiagnose.log']}. Reason: {str(e)}")

        # Save JSON file
        case_fname = os.path.join(self.config.data_folder, f"{case_id}.json")
        with open(case_fname, 'w') as data_file:
            data_file.write(json.dumps(new_case_json, indent=4))

        # update cases list file
        remotectl_dumpstate_json = remotectl_dumpstate.RemotectlDumpstateParser(self.config, case_id).get_result()
        try:
            case['serial_number'] = remotectl_dumpstate_json['Local device']['Properties']['SerialNumber']
            case['unique_device_id'] = remotectl_dumpstate_json['Local device']['Properties']['UniqueDeviceID']
        except (KeyError, TypeError) as e:
            print(f"WARNING: Could not parse remotectl_dumpstate, and therefore extract serial numbers. Error {e}")

        # update case with new data
        with open(self.config.cases_file, 'r+') as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)        # enable lock
                self._cases = json.load(f)           # load latest version
                self._cases[case['case_id']] = case  # update own case
                f.seek(0)                            # go back to the beginning of the file
                json.dump(self._cases, f, indent=4)  # save the updated version
                f.truncate()                         # truncate the rest of the file ensuring no old data is left
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)        # release lock whatever happens

        print("Sysdiagnose file has been processed")
        print(f"Case ID: {str(case['case_id'])}")
        return case['case_id']

    def parse(self, parser: str, case_id: str):
        # Load parser module
        module = importlib.import_module(f'parsers.{parser}')
        parser_instance = None
        # figure out the class name and create an instance of it
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, BaseParserInterface) and obj is not BaseParserInterface:
                parser_instance: BaseParserInterface = obj(config=self.config, case_id=case_id)
                break
        if not parser_instance:
            raise NotImplementedError(f"Parser '{parser}' does not exist or has problems")

        parser_instance.save_result(force=True)  # force parsing
        return 0

    def analyse(self, analyser: str, case_id: str):
        module = importlib.import_module(f'analysers.{analyser}')
        analyser_instance = None
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, BaseAnalyserInterface) and obj is not BaseAnalyserInterface:
                analyser_instance: BaseAnalyserInterface = obj(config=self.config, case_id=case_id)
                break
        if not analyser_instance:
            raise NotImplementedError(f"Analyser '{analyser}' does not exist or has problems")

        analyser_instance.save_result(force=True)  # force parsing

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
        fname = os.path.join(self.config.parsers_folder, f'{name}.py')
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
        fname = os.path.join(self.config.analysers_folder, f'{name}.py')
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
        modules = glob.glob(os.path.join(self.config.parsers_folder, '*.py'))
        results = {}
        for item in modules:
            if item.endswith('__init__.py'):
                continue
            try:
                name = os.path.splitext(os.path.basename(item))[0]
                module = importlib.import_module(f'parsers.{name}')
                # figure out the class name
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if isinstance(obj, type) and issubclass(obj, BaseParserInterface) and obj is not BaseParserInterface:
                        results[name] = obj.description
                        break
            except AttributeError:
                continue

        results = dict(sorted(results.items()))
        return results

    def get_analysers(self) -> dict:
        modules = glob.glob(os.path.join(self.config.analysers_folder, '*.py'))
        results = {}
        for item in modules:
            if item.endswith('__init__.py'):
                continue
            try:
                name = os.path.splitext(os.path.basename(item))[0]
                module = importlib.import_module(f'analysers.{name}')
                # figure out the class name
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if isinstance(obj, type) and issubclass(obj, BaseAnalyserInterface) and obj is not BaseAnalyserInterface:
                        results[name] = obj.description
                        break
            except AttributeError:
                continue

        results = dict(sorted(results.items()))
        return results

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
