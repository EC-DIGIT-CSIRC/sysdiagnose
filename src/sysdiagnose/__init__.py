from curses import meta
import shutil
from tabulate import tabulate
import hashlib
import importlib.util
import json
import os
import re
import tarfile
from pathlib import Path
from datetime import timezone
from sysdiagnose.parsers import iodevicetree, ioservice
from sysdiagnose.utils.base import BaseInterface, BaseParserInterface, BaseAnalyserInterface, SysdiagnoseConfig
from sysdiagnose.utils.logger import set_json_logging, logger
from io import TextIOWrapper
from sysdiagnose.utils.lock import FileLock
from sysdiagnose.utils.case import SysdiagnoseCase, SysdiagnoseCaseLibrary


class Sysdiagnose:
    def __init__(self, cases_path=os.getenv('SYSDIAGNOSE_CASES_PATH', './cases')):
        self._cases = False   # will be populated through cases() method
        self.config: SysdiagnoseConfig = SysdiagnoseConfig(cases_path)

    def cases(self, force: bool = False) -> SysdiagnoseCaseLibrary:
        # kinda caching, so it's not loaded unless necessary
        # load cases + migration of old cases format to new format
        if not self._cases or force:
            self._cases = SysdiagnoseCaseLibrary(self.config)
        return self._cases

    def create_case(self, sysdiagnose_file: str, force: bool = False, case_id: bool | str = False, tags: list[str] = None) -> str:
        '''
        Extracts the sysdiagnose file and creates a new case.

        Parameters:
            sysdiagnose_file (str): Path to the sysdiagnose file.
            force (bool): Whether to force the creation of a new case.
            case_id (str): The case ID to use, or False to generate a new incremental one.
            tags (list): List of tags to add to the case.

        Returns:
            str: The case ID of the new case.
        '''
        metadata = Sysdiagnose.get_case_metadata(sysdiagnose_file)

        if not metadata:
            raise ValueError(f"Invalid sysdiagnose file: {sysdiagnose_file}. Case could not be created!")

        # Generate case_id if not provided
        if not case_id:
            # Default suggestion for case_id is the serial number + date
            case_id = metadata['case_id']
            if self.cases().case_exists(case_id):
                # if the case_id already exists, generate incremental one
                case_id = self.cases().get_next_case_id()

        # Create SysdiagnoseCase object
        case = SysdiagnoseCase(
            case_id=str(case_id),
            tags=tags if tags else [],
            case_metadata=metadata
        )

        # Add case to library (this handles duplicate checking)
        self.cases().add_case(case, force=force)

        # create case folder and extract files
        case_data_folder = self.config.get_case_data_folder(str(case_id))
        os.makedirs(case_data_folder, exist_ok=True)
        self.extract_sysdiagnose_files(sysdiagnose_file, case_data_folder)

        print(f"Sysdiagnose file has been processed: {sysdiagnose_file}")
        return str(case_id)

    @staticmethod
    def get_case_metadata(source_file: str) -> dict | None:
        """
        Returns the metadata related to the given sysdiagnose file/folder.
        This includes serial number, unique device ID, iOS version, model, date of sysdiagnose creation,
        and a case ID based on the serial number and date.

        :param source_file: Path to the sysdiagnose file/folder
        :return: dictionary with metadata or None if the file is invalid
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
                        member_path = Path(member.name)
                        if member_path.name == 'remotectl_dumpstate.txt':
                            remotectl_dumpstate_file = tf.extractfile(member)
                            remotectl_dumpstate_file_content = remotectl_dumpstate_file.read().decode()
                            remotectl_dumpstate_json = RemotectlDumpstateParser.parse_file_content(remotectl_dumpstate_file_content)
                        elif member_path.name == 'sysdiagnose.log':
                            sysdiagnose_log_file = TextIOWrapper(tf.extractfile(member))
                            sysdiagnose_date = BaseInterface.get_sysdiagnose_creation_datetime_from_file(sysdiagnose_log_file)
                        elif member_path.name == 'SystemVersion.plist':
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
        # Turn the sysdiagnose date into UTC
        sysdiagnose_date_utc = sysdiagnose_date.astimezone(timezone.utc)
        if remotectl_dumpstate_json and 'error' not in remotectl_dumpstate_json:
            if 'Local device' in remotectl_dumpstate_json:
                try:
                    serial_number = remotectl_dumpstate_json['Local device']['Properties']['SerialNumber']
                    metadata = {
                        'serial_number': serial_number,
                        'unique_device_id': remotectl_dumpstate_json['Local device']['Properties']['UniqueDeviceID'],
                        'ios_version': remotectl_dumpstate_json['Local device']['Properties']['OSVersion'],
                        'model': remotectl_dumpstate_json['Local device']['Properties']['ProductType'],
                        'date': sysdiagnose_date_utc.isoformat(timespec='microseconds'),
                        'case_id': f"{serial_number}_{sysdiagnose_date_utc.strftime('%Y%m%d_%H%M%S')}",
                        'source_file': source_file
                    }
                    metadata['source_sha256'] = Sysdiagnose.calculate_metadata_signature(metadata)

                    return metadata
                except Exception:
                    logger.error("Could not parse remotectl_dumpstate, and therefore extract serial numbers.", exc_info=True)
            else:
                logger.error("remotectl_dumpstate does not contain a Local device section.")
        else:
            try:
                from  sysdiagnose.parsers.iodevicetree import  IODeviceTreeParser
                from  sysdiagnose.parsers.ioservice import  IOServiceParser
                iodevicetree = IODeviceTreeParser.parse_file(os.path.join(source_file, 'ioreg/IODeviceTree.txt'))
                ioservicetree = IOServiceParser.parse_file(os.path.join(source_file, 'ioreg/IOService.txt'))

                serial_number = iodevicetree['IOKitDiagnostics']['Classes']['device-tree']['IOPlatformSerialNumber']
                unique_device_id = iodevicetree['IOKitDiagnostics']['Classes']['device-tree']['IOPlatformUUID']

                # NOTE: there are many reference of the actual model in IOService.txt file
                model = ioservicetree["IOKitDiagnostics"]["model"]
                model = model.replace("<", "").replace(">", "").strip()
                metadata = {
                    'serial_number': serial_number,
                    'unique_device_id': unique_device_id,
                    'ios_version': sys_json['ProductVersion'],
                    'model': model,
                    'date': sysdiagnose_date_utc.isoformat(timespec='microseconds'),
                    'case_id': f"{serial_number}_{sysdiagnose_date_utc.strftime('%Y%m%d_%H%M%S')}",
                    'source_file': source_file
                }
                metadata['source_sha256'] = Sysdiagnose.calculate_metadata_signature(metadata)


                # FIXME use the IOService or IODeviceTree parser to get the data if remotectl_dumpstate is not available
                # FIXME also write tests...

                return metadata
            except Exception:
                logger.error("Could not parse IODeviceTree or IOService, and therefore extract missing information.", exc_info=True)
                return None



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
        for case in self.cases().get_cases().values():
            line = [
                case.case_id,
                case.case_metadata.get('date', '<unknown>'),
                case.case_metadata.get('serial_number', '<unknown>'),
                case.case_metadata.get('unique_device_id', '<unknown>'),
                case.case_metadata.get('ios_version', '<unknown>'),
                ','.join(case.tags)
            ]
            if verbose:
                line.append(case.case_metadata.get('source_file', '<unknown>'))
            lines.append(line)

        print(tabulate(lines, headers=headers))

    def get_case_ids(self):
        case_ids = list(self.cases().get_cases().keys())
        case_ids.sort()
        return case_ids

    def is_valid_case_id(self, case_id):
        return self.cases().case_exists(case_id)

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
