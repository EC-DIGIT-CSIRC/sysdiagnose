import glob
import importlib
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC
from datetime import datetime as datetime_datetime
from enum import StrEnum
from functools import cached_property
from io import TextIOWrapper
from pathlib import Path

from sysdiagnose.utils.logger import logger


class SysdiagnoseConfig:
    def __init__(self, cases_path: str):
        self.config_folder = str(Path(os.path.dirname(os.path.abspath(__file__))).parent)
        self.parsers_folder = os.path.join(self.config_folder, "parsers")
        self.analysers_folder = os.path.join(self.config_folder, "analysers")

        # case data is in current working directory by default
        self.cases_root_folder = cases_path
        self.cases_file = os.path.join(self.cases_root_folder, "cases.json")
        os.makedirs(self.cases_root_folder, exist_ok=True)

    def get_case_root_folder(self, case_id: str) -> str:
        case_root_folder = os.path.join(self.cases_root_folder, case_id)
        os.makedirs(case_root_folder, exist_ok=True)
        return case_root_folder

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

    def get_parsers(self) -> dict:
        modules = glob.glob(os.path.join(self.parsers_folder, '*.py'))
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
        modules = glob.glob(os.path.join(self.analysers_folder, '*.py'))
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


class ExecutionStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ResultSummary:
    """
    Class that represents a summary of the invocation of a BaseParserInterface or BaseAnalyserInterface subclass.

    The summary includes the status of the execution (e.g. OK, WARNING, ERROR), the execution timing metadata,
    and the number of errors, warnings, and events that were encountered during the execution.

    By default, the status is set to ERROR, the timing metadata is unknown, and the number of errors, warnings,
    and events are set to 0.
    """
    status: ExecutionStatus = ExecutionStatus.ERROR
    start_time: str | None = None
    duration: float | None = None
    num_errors: int = 0
    num_warnings: int = 0
    num_events: int = 0

    def to_dict(self) -> dict:
        return {
            'status': self.status.value,
            'start_time': self.start_time,
            'duration': self.duration,
            'num_errors': self.num_errors,
            'num_warnings': self.num_warnings,
            'num_events': self.num_events,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ResultSummary':
        status = data.get('status', ExecutionStatus.ERROR)
        return cls(
            status=ExecutionStatus(status),
            start_time=data.get('start_time'),
            duration=data.get('duration'),
            num_errors=data.get('num_errors', 0),
            num_warnings=data.get('num_warnings', 0),
            num_events=data.get('num_events', 0),
        )


class ResultSummaryLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.num_errors = 0
        self.num_warnings = 0

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            self.num_errors += 1
        elif record.levelno >= logging.WARNING:
            self.num_warnings += 1


class ResultSummaryFactory:
    @staticmethod
    def from_result(result: list | dict | str | None) -> ResultSummary:
        num_errors = ResultSummaryFactory.count_errors_in_result(result)
        num_events = ResultSummaryFactory.count_events_in_result(result)
        return ResultSummary(
            status=ResultSummaryFactory.get_execution_status(num_errors=num_errors, num_warnings=0),
            start_time=None,
            duration=None,
            num_errors=num_errors,
            num_warnings=0,
            num_events=num_events,
        )

    @staticmethod
    def from_output(output_file: str, format_name: str, result: list | dict | str | None = None) -> ResultSummary:
        if format_name == 'jsonl' and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            with open(output_file, 'r') as f:
                num_events = sum(1 for line in f if line.strip())
            return ResultSummary(status=ExecutionStatus.OK, num_events=num_events)

        if result is not None:
            return ResultSummaryFactory.from_result(result)

        with open(output_file, 'r') as f:
            if format_name == 'json':
                loaded_result = json.load(f)
            elif format_name == 'jsonl':
                loaded_result = [json.loads(line) for line in f]
            else:
                loaded_result = f.read()
        return ResultSummaryFactory.from_result(loaded_result)

    @staticmethod
    def get_execution_status(num_errors: int, num_warnings: int) -> ExecutionStatus:
        if num_errors > 0:
            return ExecutionStatus.ERROR
        if num_warnings > 0:
            return ExecutionStatus.WARNING
        return ExecutionStatus.OK

    @staticmethod
    def count_events_in_result(result: list | dict | str | None) -> int:
        if result is None:
            return 0
        if isinstance(result, list):
            return len(result)
        return 1 if result else 0

    @staticmethod
    def count_errors_in_result(result: list | dict | str | None) -> int:
        if not isinstance(result, dict):
            return 0

        num_errors = 0
        if ResultSummaryFactory.has_error_value(result.get('error')):
            num_errors += ResultSummaryFactory.count_error_value(result.get('error'))
        if ResultSummaryFactory.has_error_value(result.get('errors')):
            num_errors += ResultSummaryFactory.count_error_value(result.get('errors'))
        return num_errors

    @staticmethod
    def has_error_value(value) -> bool:
        if value is None:
            return False
        if isinstance(value, (list, tuple, set, dict, str)):
            return len(value) > 0
        return bool(value)

    @staticmethod
    def count_error_value(value) -> int:
        if isinstance(value, dict):
            return len(value)
        if isinstance(value, (list, tuple, set)):
            return len(value)
        if value:
            return 1
        return 0


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
        self.summary_file = os.path.join(self.case_parsed_data_folder, self.module_name + '.summary.json')

        self._result: list | dict | str | None = None  # empty result set, used for caching
        self._result_summary: ResultSummary | None = None

    @cached_property
    def sysdiagnose_creation_datetime(self) -> datetime_datetime:
        """
        Returns the creation date and time of the sysdiagnose as a datetime object.

        Returns:
            datetime: The creation date and time of the sysdiagnose.
        """
        return BaseInterface.get_sysdiagnose_creation_datetime_from_file(os.path.join(self.case_data_subfolder, 'sysdiagnose.log'))

    @staticmethod
    def get_sysdiagnose_creation_datetime_from_file(file: str | TextIOWrapper) -> datetime_datetime:
        """
        Returns the creation date and time of the sysdiagnose as a datetime object.

        Args:
            file (str|TextIOWrapper): The path to the sysdiagnose log file or a file object.

        Returns:
            datetime: The creation date and time of the sysdiagnose.
        """
        need_to_close = False
        if isinstance(file, str):
            f = open(file, 'r')
            need_to_close = True
        else:
            f = file
        # now we need to find the timestamp in the sysdiagnose.log file
        try:
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
                        parsed_timestamp = datetime_datetime.strptime(timestamp, "%Y.%m.%d_%H-%M-%S%z")
                        return parsed_timestamp

            raise ValueError("Invalid timestamp format in sysdiagnose.log. Cannot figure out time of sysdiagnose creation.")
        finally:
            if need_to_close:
                f.close()

    def output_exists(self) -> bool:
        """
        Checks if the output file or exists, which means the parser already ran.

        WARNING: You may need to overwrite this method if your parser saves multiple files.

        Returns:
            bool: True if the output file exists, False otherwise.
        """
        return os.path.exists(self.output_file) and os.path.getsize(self.output_file) > 0

    def get_result(self, force: bool = False) -> list | dict | str | None:
        """
        Retrieves the result of the parsing operation, and run the parsing if necessary.
        Also ensures the execution status is updated, the result is saved to the output_file, and can be used as a cache.

        Args:
            force (bool, optional): If True, forces the parsing operation even if the output cache or file exists.
            Defaults to False.

        Returns:
            list | dict: The parsed result as a list or dictionary.

        Raises:
            FileNotFoundError: If the output file does not exist and force is set to False.

        WARNING: You may need to overwrite this method if your parser saves multiple files.
        """
        if force:
            self.save_result(force=True)
            return self._result

        if self._result is None:
            if self.output_exists():
                self._result = self._load_output()
                self._result_summary = self.load_result_summary()
            else:
                self.save_result()

        return self._result

    def get_result_summary(self) -> ResultSummary:
        """
        Returns a summary of the result of the get_result operation, including the execution status, number of errors,
        warnings, and events.

        Returns:
            ResultSummary: A summary of the result of the get_result operation.
        """
        if self._result_summary is not None:
            return self._result_summary

        self._result_summary = self.load_result_summary()
        return self._result_summary

    def load_result_summary(self) -> ResultSummary:
        if os.path.exists(self.summary_file) and os.path.getsize(self.summary_file) > 0:
            with open(self.summary_file, 'r') as f:
                return ResultSummary.from_dict(json.load(f))

        if self.output_exists():
            return ResultSummaryFactory.from_output(self.output_file, self.format, self._result)

        return ResultSummary()

    def save_result(self, force: bool = False, indent=None):
        """
        Saves the result of the parsing operation to a file and returns the execution status.

        Args:
            force (bool, optional): If True, forces the parsing operation even if the output cache or file exists. Defaults to False.
            indent (int, optional): The number of spaces to use for indentation in the JSON output. Defaults to None.

        WARNING: You may need to overwrite this method if your parser saves multiple files.
        """
        if force or self._result is None or not self.output_exists():
            self._result = self.execute_with_result_summary()
        elif self._result_summary is None:
            self._result_summary = self.load_result_summary()

        with open(self.output_file, 'w') as f:
            if self.format == 'json':
                # json.dumps is MUCH faster than json.dump, but less efficient on memory level
                # also no indent as that's terribly slow
                if self.json_pretty:
                    f.write(json.dumps(self._result, ensure_ascii=False, indent=2, sort_keys=True))
                else:
                    f.write(json.dumps(self._result, ensure_ascii=False, indent=indent))
            elif self.format == 'jsonl':
                for line in self._result:
                    f.write(json.dumps(line, ensure_ascii=False, indent=indent))
                    f.write('\n')
            else:
                f.write(self._result)

        self.save_result_summary()

    def save_result_summary(self) -> None:
        if self._result_summary is None:
            self._result_summary = ResultSummaryFactory.from_result(self._result)

        with open(self.summary_file, 'w') as f:
            json.dump(self._result_summary.to_dict(), f, ensure_ascii=False, indent=2, sort_keys=True)

    def execute_with_result_summary(self) -> list | dict | str | None:
        log_handler = ResultSummaryLogHandler()
        start_time = datetime_datetime.now(UTC)
        logger.addHandler(log_handler)
        try:
            result = self.execute()
        except Exception:
            duration = (datetime_datetime.now(UTC) - start_time).total_seconds()
            self._result_summary = ResultSummary(
                status=ExecutionStatus.ERROR,
                start_time=start_time.isoformat(timespec='microseconds'),
                duration=duration,
                num_errors=max(1, log_handler.num_errors),
                num_warnings=log_handler.num_warnings,
                num_events=0,
            )
            raise
        finally:
            logger.removeHandler(log_handler)

        summary = (
            ResultSummaryFactory.from_output(self.output_file, self.format, self._result)
            if result is None and self.output_exists()
            else ResultSummaryFactory.from_result(result)
        )
        summary.start_time = start_time.isoformat(timespec='microseconds')
        summary.duration = (datetime_datetime.now(UTC) - start_time).total_seconds()
        summary.num_errors += log_handler.num_errors
        summary.num_warnings += log_handler.num_warnings
        summary.status = ResultSummaryFactory.get_execution_status(summary.num_errors, summary.num_warnings)
        self._result_summary = summary
        return result

    def _load_output(self) -> list | dict | str | None:
        with open(self.output_file, 'r') as f:
            if self.format == 'json':
                return json.load(f)
            if self.format == 'jsonl':
                return [json.loads(line) for line in f]
            return f.read()

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

    def contains_timestamp(self):
        """
            Returns true if the parser contains a timestamp
        """
        return self.format == "jsonl"


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


@dataclass(order=True)
class Event():
    datetime: datetime_datetime  # timestamp of the event
    message: str    # human-readable message
    module: str     # module name (e.g. "crashlogs")

    timestamp_desc: str = ''   # description of the timestamp (e.g. "sysdiagnose creation time")
    data: dict = field(default_factory=dict)         # dict with the data of the event

    # allows access to the attributes as if they were dictionary keys
    def __getitem__(self, key):
        if key == 'datetime':
            # return the timestamp as a datetime str
            return self.datetime.isoformat(timespec='microseconds')
        elif key == 'timestamp':  # temporary backwards compatibility
            # return the timestamp as a timestamp int
            return int(self.datetime.timestamp())
        return getattr(self, key)

    # allows access to the attributes as if they were dictionary keys
    def __setitem__(self, key, value):
        if key == 'datetime':
            if isinstance(value, str):
                # if the value is a string, try to parse it as a datetime
                try:
                    value = datetime_datetime.fromisoformat(value)
                except ValueError as e:
                    logger.error(f"Invalid timestamp format: {value}")
                    raise ValueError("Invalid timestamp format, expected ISO 8601 format.") from e
            elif isinstance(value, datetime_datetime):
                # if the value is already a datetime, just use it
                pass
            else:
                logger.error(f"Invalid timestamp type: {type(value)}")
                raise TypeError("Timestamp must be a datetime object or an ISO 8601 formatted string.")

        return setattr(self, key, value)

    def to_json(self) -> str:
        """
        Converts the Event object to a JSON string.

        Returns:
            str: A JSON string representation of the Event object.
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def to_dict(self) -> dict:
        """
        Converts the Event object to a dictionary.

        Returns:
            dict: A dictionary representation of the Event object.
        """

        output = {}
        # keep this last as this ensures the mandatory fields have precedence
        output.update({
            'datetime': self.datetime.isoformat(timespec='microseconds'),
            'message': self.message,
            'timestamp_desc': self.timestamp_desc,
            'module': self.module,
            'data': self.data
        })
        return output

    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        """
        Populates the Event object from a dictionary.

        Args:
            data (dict): A dictionary containing the event data.
        """
        try:
            datetime = datetime_datetime.fromisoformat(data.get('datetime', ''))
        except Exception:
            try:
                datetime = datetime_datetime.fromtimestamp(data.get('timestamp', ''), tz=UTC)
            except Exception as e:
                logger.error(f"Failed to parse timestamp: {e}", exc_info=True)
                raise ValueError("Invalid timestamp format in data dictionary: no isoformat datetime or timestamp int.") \
                    from e

        message = data.get('message', '')
        module = data.get('module', '')
        event = cls(datetime=datetime, message=message, module=module)
        event.timestamp_desc = data.get('timestamp_desc', '')
        event.data = data.get('data', {})
        return event
