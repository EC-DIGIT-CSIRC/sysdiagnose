from tabulate import tabulate
import glob
import hashlib
import importlib.util
import json
import os
import re
import tarfile
import fcntl
from sysdiagnose.utils.base import BaseParserInterface, BaseAnalyserInterface, SysdiagnoseConfig


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
        from sysdiagnose.parsers import remotectl_dumpstate

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
                'date': '<unknown>',  # date when sysdiagnose was taken
                'case_id': case_id,
                'source_file': sysdiagnose_file,
                'source_sha256': readable_hash,
                'serial_number': '<unknown>',
                'unique_device_id': '<unknown>',
                'ios_version': '<unknown>',
                'tags': []
            }

        # create case folder
        case_data_folder = self.config.get_case_data_folder(str(case['case_id']))
        os.makedirs(case_data_folder, exist_ok=True)

        # extract sysdiagnose files
        try:
            tf.extractall(path=case_data_folder, filter=None)
        except Exception as e:
            raise Exception(f'Error while decompressing sysdiagnose file. Reason: {str(e)}')

        try:
            tf.close()
        except Exception as e:
            raise Exception(f'Error closing sysdiagnose file. Reason: {str(e)}')

        # update cases metadata
        remotectl_dumpstate_parser = remotectl_dumpstate.RemotectlDumpstateParser(self.config, case_id)
        remotectl_dumpstate_json = remotectl_dumpstate_parser.get_result()
        try:
            case['serial_number'] = remotectl_dumpstate_json['Local device']['Properties']['SerialNumber']
            case['unique_device_id'] = remotectl_dumpstate_json['Local device']['Properties']['UniqueDeviceID']
            case['version'] = remotectl_dumpstate_json['Local device']['Properties']['OSVersion']
        except (KeyError, TypeError) as e:
            print(f"WARNING: Could not parse remotectl_dumpstate, and therefore extract serial numbers. Error {e}")

        try:
            case['date'] = remotectl_dumpstate_parser.sysdiagnose_creation_datetime.isoformat()
        except Exception:
            pass

        # update case with new data
        with open(self.config.cases_file, 'r+') as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)        # enable lock
                self._cases = json.load(f)           # load latest version
                self._cases[case['case_id']] = case  # update own case
                f.seek(0)                            # go back to the beginning of the file
                json.dump(self._cases, f, indent=4, sort_keys=True)  # save the updated version
                f.truncate()                         # truncate the rest of the file ensuring no old data is left
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)        # release lock whatever happens

        print("Sysdiagnose file has been processed")
        print(f"Case ID: {str(case['case_id'])}")
        return case

    def parse(self, parser: str, case_id: str):
        # Load parser module
        module = importlib.import_module(f'sysdiagnose.parsers.{parser}')
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
        module = importlib.import_module(f'sysdiagnose.analysers.{analyser}')
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

    def print_list_cases(self, verbose=False):
        print("#### case List ####")
        headers = ['Case ID', 'acquisition date', 'Serial number', 'Unique device ID', 'iOS Version', 'Tags']
        if verbose:
            headers.append('Source file')
        lines = []
        for case in self.cases().values():
            line = [
                case['case_id'],
                case.get('date', '<unknown>'),
                case.get('serial_number', '<unknown>'),
                case.get('unique_device_id', '<unknown>'),
                case.get('ios_version', '<unknown>'),
                ','.join(case.get('tags', []))
            ]
            if verbose:
                line.append(case['source_file'])
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
                module = importlib.import_module(f'sysdiagnose.parsers.{name}')
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
                module = importlib.import_module(f'sysdiagnose.analysers.{name}')
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
