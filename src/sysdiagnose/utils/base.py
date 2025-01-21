from abc import ABC, abstractmethod
from datetime import datetime
from functools import cached_property
from pathlib import Path
from sysdiagnose.utils.logger import logger
import glob
import json
import os
import re


class SysdiagnoseConfig:
    def __init__(self, cases_path: str):
        self.config_folder = str(Path(os.path.dirname(os.path.abspath(__file__))).parent)
        self.parsers_folder = os.path.join(self.config_folder, "parsers")
        self.analysers_folder = os.path.join(self.config_folder, "analysers")

        # case data is in current working directory by default
        self.cases_root_folder = cases_path
        self.cases_file = os.path.join(self.cases_root_folder, "cases.json")
        os.makedirs(self.cases_root_folder, exist_ok=True)

    def get_case_data_folder(self, case_id: str) -> str:
        case_data_folder = os.path.join(self.cases_root_folder, case_id, 'data')
        os.makedirs(case_data_folder, exist_ok=True)
        return case_data_folder

    def get_case_parsed_data_folder(self, case_id: str) -> str:
        parsed_data_folder = os.path.join(self.cases_root_folder, case_id, 'parsed_data')
        os.makedirs(parsed_data_folder, exist_ok=True)
        return parsed_data_folder

    def get_case_log_data_folder(self, case_id: str) -> str:
        logs_data_folder = os.path.join(self.cases_root_folder, case_id, 'logs')
        os.makedirs(logs_data_folder, exist_ok=True)
        return logs_data_folder


class BaseInterface(ABC):

    description = '<not documented>'  # implementation should set this
    format = 'json'  # implementation should set this
    json_pretty = True  # implementation should set this to false for large data sets

    def __init__(self, module_filename: str, config: SysdiagnoseConfig, case_id: str):
        self.config = config

        self.module_name = os.path.basename(module_filename).split('.')[0]
        self.case_id = case_id

        self.case_data_folder = config.get_case_data_folder(case_id)
        os.makedirs(self.case_data_folder, exist_ok=True)

        # Search for the 'sysdiagnose.log' file and return the parent folder
        log_files = glob.glob(os.path.join(self.case_data_folder, '**', 'sysdiagnose.log'), recursive=True)
        if log_files:
            self.case_data_subfolder = os.path.dirname(log_files[0])
        else:
            self.case_data_subfolder = self.case_data_folder

        self.case_parsed_data_folder = config.get_case_parsed_data_folder(case_id)
        os.makedirs(self.case_parsed_data_folder, exist_ok=True)

        if not os.path.isdir(self.case_data_folder):
            logger.error(f"Case {case_id} does not exist")
            raise FileNotFoundError(f"Case {case_id} does not exist")

        self.output_file = os.path.join(self.case_parsed_data_folder, self.module_name + '.' + self.format)

        self._result: dict | list = None  # empty result set, used for caching

    @cached_property
    def sysdiagnose_creation_datetime(self) -> datetime:
        """
        Returns the creation date and time of the sysdiagnose as a datetime object.

        Returns:
            datetime: The creation date and time of the sysdiagnose.
        """
        with open(os.path.join(self.case_data_subfolder, 'sysdiagnose.log'), 'r') as f:
            timestamp_regex = None
            for line in f:
                if 'IN_PROGRESS_sysdiagnose' in line:
                    timestamp_regex = r"IN_PROGRESS_sysdiagnose_(\d{4}\.\d{2}\.\d{2}_\d{2}-\d{2}-\d{2}[\+,-]\d{4})_"
                elif 'spindump_sysdiagnose_' in line:
                    timestamp_regex = r"spindump_sysdiagnose_(\d{4}\.\d{2}\.\d{2}_\d{2}-\d{2}-\d{2}[\+,-]\d{4})_"
                if timestamp_regex:
                    match = re.search(timestamp_regex, line)
                    if match:
                        timestamp = match.group(1)
                        parsed_timestamp = datetime.strptime(timestamp, "%Y.%m.%d_%H-%M-%S%z")
                        return parsed_timestamp
                    else:
                        raise ValueError("Invalid timestamp format in sysdiagnose.log. Cannot figure out time of sysdiagnose creation.")

    def output_exists(self) -> bool:
        """
        Checks if the output file or exists, which means the parser already ran.

        WARNING: You may need to overwrite this method if your parser saves multiple files.

        Returns:
            bool: True if the output file exists, False otherwise.
        """
        return os.path.exists(self.output_file) and os.path.getsize(self.output_file) > 0

    def get_result(self, force: bool = False) -> list | dict:
        """
        Retrieves the result of the parsing operation, and run the parsing if necessary.
        Also ensures the result is saved to the output_file, and can be used as a cache.

        Args:
            force (bool, optional): If True, forces the parsing operation even if the output cache or file exists. Defaults to False.

        Returns:
            list | dict: The parsed result as a list or dictionary.

        Raises:
            FileNotFoundError: If the output file does not exist and force is set to False.

        WARNING: You may need to overwrite this method if your parser saves multiple files.
        """
        if force:
            # force parsing
            self._result = self.execute()
            # content has changed, save it
            self.save_result()

        if self._result is None:
            if self.output_exists():
                logger.info("Using cached results")
                # load existing output
                with open(self.output_file, 'r') as f:
                    if self.format == 'json':
                        self._result = json.load(f)
                    elif self.format == 'jsonl':
                        self._result = [json.loads(line) for line in f]
                    else:
                        self._result = f.read()
            else:
                # output does not exist, and we don't have a result yet
                self._result = self.execute()
                # content has changed, save it
                self.save_result()

        return self._result

    def save_result(self, force: bool = False, indent=None):
        """
        Saves the result of the parsing operation to a file.

        Args:
            force (bool, optional): If True, forces the parsing operation even if the output cache or file exists. Defaults to False.

        WARNING: You may need to overwrite this method if your parser saves multiple files.
        """
        # save to file
        with open(self.output_file, 'w') as f:
            if self.format == 'json':
                # json.dumps is MUCH faster than json.dump, but less efficient on memory level
                # also no indent as that's terribly slow
                if self.json_pretty:
                    f.write(json.dumps(self.get_result(force), ensure_ascii=False, indent=2, sort_keys=True))
                else:
                    f.write(json.dumps(self.get_result(force), ensure_ascii=False, indent=indent))
            elif self.format == 'jsonl':
                for line in self.get_result(force):
                    f.write(json.dumps(line, ensure_ascii=False, indent=indent))
                    f.write('\n')
            else:
                f.write(self.get_result(force))

    @abstractmethod
    def execute(self) -> list | dict:
        """
        This method is responsible for executing the functionality of the class.

        Returns:
            list | dict: The result of the execution.
        """

        # When implementing a parser, make sure you use the self.get_log_files() method to get the log files,
        # and then process those files using the magic you have implemented.
        pass


class BaseParserInterface(BaseInterface):

    def __init__(self, module_filename: str, config: SysdiagnoseConfig, case_id: str):
        super().__init__(module_filename, config, case_id)

    @abstractmethod
    def get_log_files(self) -> list:
        """
        Retrieves the log files used by this parser.

        Returns:
            list: A list of log files that exist.
        """
        pass


class BaseAnalyserInterface(BaseInterface):
    def __init__(self, module_filename: str, config: SysdiagnoseConfig, case_id: str):
        super().__init__(module_filename, config, case_id)
