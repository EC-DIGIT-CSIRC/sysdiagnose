import shutil
from tabulate import tabulate
import hashlib
import importlib.util
import json
import os
import re
import tarfile
from sysdiagnose.utils.base import BaseInterface, BaseParserInterface, BaseAnalyserInterface, SysdiagnoseConfig
from sysdiagnose.utils.logger import set_json_logging, logger
from io import TextIOWrapper
from sysdiagnose.utils.lock import FileLock


class Sysdiagnose:
    def __init__(self, cases_path=os.getenv('SYSDIAGNOSE_CASES_PATH', './cases')):
        self._cases = False   # will be populated through cases() singleton method
        self.config: SysdiagnoseConfig = SysdiagnoseConfig(cases_path)

    def cases(self, force: bool = False) -> dict:
        # pseudo singleton, so it's not loaded unless necessary
        # load cases + migration of old cases format to new format
        if not self._cases or force:
            try:
                FileLock.acquire_lock(self.config.cases_file)
                with open(self.config.cases_file, 'r+') as f:
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
            except FileNotFoundError:
                self._cases = {}
                with open(self.config.cases_file, 'w') as f:
                    json.dump(self._cases, f, indent=4)
            finally:
                FileLock.release_lock(self.config.cases_file)

        return self._cases

    def delete_case(self, case_id: str) -> None:
        '''
        Deletes a case from the sysdiagnose cases.

        Parameters:
            case_id (str): The case ID to delete.
        '''
        # check if case_id is valid
        if case_id not in self.cases():
            raise ValueError(f"Case ID {case_id} does not exist.")

        # delete case folder
        case_folder = os.path.join(self.config.cases_root_folder, case_id)
        if os.path.isdir(case_folder):
            try:
                shutil.rmtree(case_folder)
            except Exception as e:
                raise Exception(f"Error while deleting case folder: {str(e)}")

        # delete case from the cases
        try:
            FileLock.acquire_lock(self.config.cases_file)
            with open(self.config.cases_file, 'r+') as f:
                self._cases = json.load(f)           # load latest version
                self._cases.pop(case_id, None)       # delete case
                f.seek(0)                            # go back to the beginning of the file
                json.dump(self._cases, f, indent=4, sort_keys=True)  # save the updated version
                f.truncate()                         # truncate the rest of the file ensuring no old data is left
        finally:
            FileLock.release_lock(self.config.cases_file)

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
        metadata = Sysdiagnose.get_case_metadata(sysdiagnose_file)

        if not metadata:
            raise ValueError(f"Invalid sysdiagnose file: {sysdiagnose_file}. Case could not be created!")

        # only allow specific chars for case_id
        if case_id:
            if not re.match(r'^[a-zA-Z0-9-_\.]+$', case_id):
                raise ValueError("Invalid case ID. Only alphanumeric and -_. characters are allowed.")

        # check if sysdiagnise file is already in a case
        case = None
        for c in self.cases().values():
            # TODO: this breaks backward compatibility of sha256 calculation from old cases
            if c['source_sha256'] == metadata['source_sha256']:
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
            # TODO: again, the sha256 calculation is not the same as the one in the old cases
            if self.cases()[case_id]['source_sha256'] != metadata['source_sha256']:
                raise ValueError(f"Case ID {case_id} already exists but with a different sysdiagnose file.")

        # find next incremental case_id, if needed
        if not case_id:
            # Default suggestion for case_id is the serial number + date
            case_id = metadata['case_id']
            if case_id in self.cases():
                # if the case_id already exists, we need to find a new one
                # find the highest case_id in the cases
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
                'date': metadata['date'],
                'case_id': case_id,
                'source_file': sysdiagnose_file,
                'source_sha256': metadata['source_sha256'],
                'serial_number': metadata['serial_number'],
                'unique_device_id': metadata['unique_device_id'],
                'ios_version': metadata['ios_version'],
                'tags': []
            }

        # create case folder
        case_data_folder = self.config.get_case_data_folder(str(case['case_id']))
        os.makedirs(case_data_folder, exist_ok=True)

        # extract sysdiagnose files
        self.extract_sysdiagnose_files(sysdiagnose_file, case_data_folder)

        # update case with new data
        try:
            FileLock.acquire_lock(self.config.cases_file)
            with open(self.config.cases_file, 'r+') as f:
                self._cases = json.load(f)           # load latest version
                self._cases[case['case_id']] = case  # update own case
                f.seek(0)                            # go back to the beginning of the file
                json.dump(self._cases, f, indent=4, sort_keys=True)  # save the updated version
                f.truncate()                         # truncate the rest of the file ensuring no old data is left
        finally:
            FileLock.release_lock(self.config.cases_file)

        print(f"Sysdiagnose file has been processed: {sysdiagnose_file}")
        return case

    @staticmethod
    def get_case_metadata(source_file: str) -> str:
        """
        Returns the sha256 hash of the sysdiagnose source file/folder.
        The hash is calculated by concatenating the contents of the case metadata: udid, serial, ios version and date.

        :param source_file: Path to the sysdiagnose file/folder
        :return: sha256 hash of the file/folder
        """
        from sysdiagnose.parsers.remotectl_dumpstate import RemotectlDumpstateParser
        from sysdiagnose.parsers.sys import SystemVersionParser

        if os.path.isfile(source_file):
            remotectl_dumpstate_json = None
            sysdiagnose_log_file = None

            # workaround for incompatible filesystem such as SMB
            targz_file = source_file
            try:
                with open(source_file, 'r+'):  # test
                    # compatible filesystem
                    pass
            except OSError:
                # incompatible filesystem, copy file locally instead
                import shutil
                import tempfile
                targz_file = tempfile.mktemp(suffix='.tar.gz')
                shutil.copyfile(source_file, targz_file)

            try:
                with tarfile.open(targz_file) as tf:
                    for member in tf.getmembers():
                        if member.name.endswith('remotectl_dumpstate.txt'):
                            remotectl_dumpstate_file = tf.extractfile(member)
                            remotectl_dumpstate_file_content = remotectl_dumpstate_file.read().decode()
                            remotectl_dumpstate_json = RemotectlDumpstateParser.parse_file_content(remotectl_dumpstate_file_content)
                        elif member.name.endswith('sysdiagnose.log'):
                            sysdiagnose_log_file = TextIOWrapper(tf.extractfile(member))
                            sysdiagnose_date = BaseInterface.get_sysdiagnose_creation_datetime_from_file(sysdiagnose_log_file)
                        elif member.name.endswith('SystemVersion.plist'):
                            sys_json_file = tf.extractfile(member)
                            sys_json_file_content = sys_json_file.read().decode()
                            sys_json = SystemVersionParser.parse_file_content(sys_json_file_content)

            except Exception as e:
                logger.error(f"File 'remotectl_dumpstate.txt' or 'sysdiagnose.log' not found in the archive {source_file}: {e}", exc_info=True)
            finally:
                if targz_file != source_file:
                    # remove the temporary file if we copied it
                    os.remove(targz_file)

        elif os.path.isdir(source_file):
            sysdiagnose_log_file = os.path.join(source_file, 'sysdiagnose.log')
            remotectl_dumpstate_file = os.path.join(source_file, 'remotectl_dumpstate.txt')
            remotectl_dumpstate_json = RemotectlDumpstateParser.parse_file(remotectl_dumpstate_file)
            sysdiagnose_date = BaseInterface.get_sysdiagnose_creation_datetime_from_file(sysdiagnose_log_file)

        else:
            logger.error(f"File {source_file} is not a valid sysdiagnose file or folder.")
            return None

        # Time to obtain the metadata

        if remotectl_dumpstate_json and 'error' not in remotectl_dumpstate_json:
            if 'Local device' in remotectl_dumpstate_json:
                try:
                    serial_number = remotectl_dumpstate_json['Local device']['Properties']['SerialNumber']
                    metadata = {
                        'serial_number': serial_number,
                        'unique_device_id': remotectl_dumpstate_json['Local device']['Properties']['UniqueDeviceID'],
                        'ios_version': remotectl_dumpstate_json['Local device']['Properties']['OSVersion'],
                        'model': remotectl_dumpstate_json['Local device']['Properties']['ProductType'],
                        'date': sysdiagnose_date.isoformat(timespec='microseconds'),
                        'case_id': f"{serial_number}_{sysdiagnose_date.strftime('%Y%m%d_%H%M%S')}",
                        'source_file': source_file,
                        'source_sha256': ''
                    }
                    metadata['source_sha256'] = Sysdiagnose.calculate_metadata_signature(metadata)

                    return metadata
                except Exception:
                    logger.error("Could not parse remotectl_dumpstate, and therefore extract serial numbers.", exc_info=True)
            else:
                logger.error("remotectl_dumpstate does not contain a Local device section.")
        else:
            # FIXME use the IOService or IODeviceTree parser to get the data if remotectl_dumpstate is not available
            # FIXME also write tests...
            serial_number = 'unknown'
            metadata = {
                'serial_number': serial_number,
                'unique_device_id': 'unknown',
                'ios_version': sys_json['ProductVersion'],
                'model': 'unknown',  # FIXME figure out a way to get the model from sysdiagnose
                'date': sysdiagnose_date.isoformat(timespec='microseconds'),
                'case_id': f"{serial_number}_{sysdiagnose_date.strftime('%Y%m%d_%H%M%S')}",
                'source_file': source_file,
                'source_sha256': ''
            }

        return None

    @staticmethod
    def calculate_metadata_signature(metadata: dict) -> str:
        """
        Calculates the signature of the metadata by concatenating all fields except 'case_id', 'source_file' and
        'source_sha256'.

        :param metadata: Dictionary containing metadata fields.
        :return: SHA256 hash of the concatenated metadata fields.
        """
        # Exclude 'case_id' and 'source_sha256' from the metadata
        excluded_keys = {'case_id', 'source_file', 'source_sha256'}
        concatenated_values = ''.join(
            str(value) for key, value in metadata.items() if key not in excluded_keys
        )

        # Calculate the SHA256 hash of the concatenated string
        signature = hashlib.sha256(concatenated_values.encode('utf-8')).hexdigest()
        return signature

    def extract_sysdiagnose_files(self, sysdiagnose_file: str, destination_folder: str) -> None:
        """
        Extracts the sysdiagnose files from the given sysdiagnose file to the specified destination folder.

        :param sysdiagnose_file: Path to the sysdiagnose file.
        :param destination_folder: Path to the destination folder where files will be extracted.
        """
        if os.path.isfile(sysdiagnose_file):
            try:
                with tarfile.open(sysdiagnose_file) as tf:
                    # Extract the sysdiagnose files to the destination folder
                    tf.extractall(path=destination_folder, filter=None)
            except TypeError:
                # python 3.11 compatibility
                try:
                    with tarfile.open(sysdiagnose_file) as tf:
                        tf.extractall(path=destination_folder)
                except Exception as e:
                    raise Exception(f'Error while decompressing sysdiagnose file {sysdiagnose_file}. Reason: {str(e)}')
            except Exception as e:
                raise Exception(f'Error while decompressing sysdiagnose file {sysdiagnose_file}. Reason: {str(e)}')

        elif os.path.isdir(sysdiagnose_file):
            try:
                shutil.copytree(sysdiagnose_file, os.path.join(destination_folder, 'sysdiagnose'), dirs_exist_ok=True)
            except Exception as e:
                raise Exception(f'Error while copying sysdiagnose folder. Reason: {str(e)}')

    def init_case_logging(self, mode: str, case_id: str) -> None:
        ''' Initialises the file handler '''
        folder = self.config.get_case_log_data_folder(case_id=case_id)
        file_path = os.path.join(folder, f'log-{mode}.jsonl')
        set_json_logging(filename=file_path)

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

    def print_parsers_list(self) -> None:
        lines = [['all', 'Run all parsers']]
        for parser, description in self.config.get_parsers().items():
            lines.append([parser, description])

        headers = ['Parser Name', 'Parser Description']
        print(tabulate(lines, headers=headers))

    def print_analysers_list(self) -> None:
        lines = [['all', 'Run all analysers']]
        for analyser, description in self.config.get_analysers().items():
            lines.append([analyser, description])

        headers = ['Analyser Name', 'Analyser Description']
        print(tabulate(lines, headers=headers))
