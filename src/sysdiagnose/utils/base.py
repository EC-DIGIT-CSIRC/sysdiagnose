import glob
import importlib
import json
import os
import re
from abc import ABC, abstractmethod
from collections.abc import Generator, Iterator
from dataclasses import dataclass, field
from datetime import UTC
from datetime import datetime as datetime_datetime
from functools import cached_property
from io import TextIOWrapper
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

from sysdiagnose.utils.logger import logger
from sysdiagnose.utils.summary import (
    ExecutionStatus,
    ResultSummary,
    ResultSummaryExecutionHandler,
)


class SysdiagnoseConfig:
    def __init__(self, cases_path: str) -> None:
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
        case_data_folder = os.path.join(self.cases_root_folder, case_id, "data")
        os.makedirs(case_data_folder, exist_ok=True)
        return case_data_folder

    def get_case_parsed_data_folder(self, case_id: str) -> str:
        parsed_data_folder = os.path.join(self.cases_root_folder, case_id, "parsed_data")
        os.makedirs(parsed_data_folder, exist_ok=True)
        return parsed_data_folder

    def get_case_log_data_folder(self, case_id: str) -> str:
        logs_data_folder = os.path.join(self.cases_root_folder, case_id, "logs")
        os.makedirs(logs_data_folder, exist_ok=True)
        return logs_data_folder

    def get_parsers(self) -> dict:
        modules = glob.glob(os.path.join(self.parsers_folder, "*.py"))
        results = {}
        for item in modules:
            if item.endswith("__init__.py"):
                continue
            try:
                name = os.path.splitext(os.path.basename(item))[0]
                module = importlib.import_module(f"sysdiagnose.parsers.{name}")
                # figure out the class name
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, BaseParserInterface)
                        and obj is not BaseParserInterface
                    ):
                        results[name] = obj.description
                        break
            except AttributeError:
                continue

        results = dict(sorted(results.items()))
        return results

    def get_analysers(self) -> dict:
        modules = glob.glob(os.path.join(self.analysers_folder, "*.py"))
        results = {}
        for item in modules:
            if item.endswith("__init__.py"):
                continue
            try:
                name = os.path.splitext(os.path.basename(item))[0]
                module = importlib.import_module(f"sysdiagnose.analysers.{name}")
                # figure out the class name
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, BaseAnalyserInterface)
                        and obj is not BaseAnalyserInterface
                    ):
                        results[name] = obj.description
                        break
            except AttributeError:
                continue

        results = dict(sorted(results.items()))
        return results


class BaseInterface(ABC):
    description = "<not documented>"  # implementation should set this
    format = "json"  # implementation should set this
    json_pretty = True  # implementation should set this to false for large data sets
    ios_version = "*"  # PEP 440 version specifier for compatible iOS versions (e.g. ">=17.0", ">=14.0,<17.0")

    def __init__(self, module_filename: str, config: SysdiagnoseConfig, case: dict) -> None:
        self.config = config

        self.module_name = os.path.basename(module_filename).split(".")[0]
        self.case = case

        self.case_data_folder = config.get_case_data_folder(self.case_id)
        os.makedirs(self.case_data_folder, exist_ok=True)

        # Search for the 'sysdiagnose.log' file and return the parent folder
        log_files = glob.glob(os.path.join(self.case_data_folder, "**", "sysdiagnose.log"), recursive=True)
        if log_files:
            self.case_data_subfolder = os.path.dirname(log_files[0])
        else:
            self.case_data_subfolder = self.case_data_folder

        self.case_parsed_data_folder = config.get_case_parsed_data_folder(self.case_id)
        os.makedirs(self.case_parsed_data_folder, exist_ok=True)

        if not os.path.isdir(self.case_data_folder):
            logger.error(f"Case {self.case_id} does not exist")
            raise FileNotFoundError(f"Case {self.case_id} does not exist")

        self.output_file = os.path.join(self.case_parsed_data_folder, self.module_name + "." + self.format)
        self.summary_file = os.path.join(
            self.config.get_case_log_data_folder(case_id=self.case_id), "summary-" + self.module_name + ".json"
        )

        self._result: list | dict | str | None = None  # empty result set, used for caching
        self._result_summary: ResultSummary | None = None

    @property
    def case_id(self) -> str | None:
        """
        Returns the case ID of the current case from the case metadata

        Returns:
            str: The string with the ID of the case, or None if unavailable
        """
        return self.case.get("case_id")

    @property
    def case_ios_version(self) -> str | None:
        """
        Returns the iOS version string for the current case from the case metadata.

        Returns:
            str | None: The iOS version string (e.g. "17.0"), or None if unavailable.
        """
        return self.case.get("ios_version")

    @property
    def case_model(self) -> str | None:
        """
        Returns the model string for the current case from the case metadata.

        Returns:
            str | None: The model string (e.g. "iPad16,3"), or None if unavailable.
        """
        return self.case.get("model")

    def is_compatible(self) -> bool:
        """
        Checks whether this parser/analyser is compatible with the given iOS version.

        Uses PEP 440 version specifiers (e.g. ">=17.0", ">=14.0,<17.0", "*").

        Returns:
            bool: True if compatible (or if compatibility cannot be determined), False otherwise.

        Raises:
            InvalidSpecifier: If the ios_version class attribute is not a valid PEP 440 specifier.
        """
        if self.ios_version == "*":
            return True

        if self.case_ios_version is None:
            # Cannot determine compatibility without a version — assume compatible
            return True

        # Invalid specifier is a developer error — let it raise
        spec = SpecifierSet(self.ios_version)

        try:
            version = Version(self.case_ios_version)
        except InvalidVersion:
            logger.warning(
                f"Could not parse iOS version '{self.case_ios_version}' for {self.module_name}, assuming compatible."
            )
            return True

        return version in spec

    @cached_property
    def sysdiagnose_creation_datetime(self) -> datetime_datetime:
        """
        Returns the creation date and time of the sysdiagnose as a datetime object.

        Returns:
            datetime: The creation date and time of the sysdiagnose.
        """
        return BaseInterface.get_sysdiagnose_creation_datetime_from_file(
            os.path.join(self.case_data_subfolder, "sysdiagnose.log")
        )

    @staticmethod
    def get_sysdiagnose_creation_datetime_from_file(file: str | TextIOWrapper) -> datetime_datetime:
        """
        Returns the creation date and time of the sysdiagnose as a datetime object.

        Args:
            file (str|TextIOWrapper): The path to the sysdiagnose log file or a file object.

        Returns:
            datetime: The creation date and time of the sysdiagnose.
        """

        def _parse(f: TextIOWrapper) -> datetime_datetime:
            for line in f:
                if "IN_PROGRESS_sysdiagnose" in line:
                    regex = r"IN_PROGRESS_sysdiagnose_(\d{4}\.\d{2}\.\d{2}_\d{2}-\d{2}-\d{2}[\+,-]\d{4})_"
                elif "spindump_sysdiagnose_" in line:
                    regex = r"spindump_sysdiagnose_(\d{4}\.\d{2}\.\d{2}_\d{2}-\d{2}-\d{2}[\+,-]\d{4})_"
                else:
                    continue

                match = re.search(regex, line)
                if match:
                    return datetime_datetime.strptime(match.group(1), "%Y.%m.%d_%H-%M-%S%z")

            raise ValueError("Invalid timestamp format...")

        if isinstance(file, str):
            with open(file) as f:
                return _parse(f)
        else:
            return _parse(file)

    def output_exists(self) -> bool:
        """
        Checks if the output file or exists, which means the parser already ran.

        WARNING: You may need to overwrite this method if your parser saves multiple files.

        Returns:
            bool: True if the output file exists, False otherwise.
        """
        return os.path.exists(self.output_file) and os.path.getsize(self.output_file) > 0

    def get_result_summary(self) -> ResultSummary:
        """
        Returns a summary of the result of the get_result operation, including the execution status, number of errors,
        warnings, and events.

        Returns:
            ResultSummary: A summary of the result of the get_result operation.
        """
        if self._result_summary is not None:
            return self._result_summary

        if os.path.exists(self.summary_file) and os.path.getsize(self.summary_file) > 0:
            with open(self.summary_file) as f:
                self._result_summary = ResultSummary.from_dict(json.load(f))
        else:
            self._result_summary = ResultSummary()

        # TODO: Detect stale results. Options considered:
        # B) Store framework version in ResultSummary — catches any change,
        #    but causes false positives from unrelated updates
        # C) Store hash of parser source in ResultSummary — precise, no false positives, survives git ops,
        #    but doesn't catch changes in dependencies (utilities, base class).
        #    Backward compatible (old summaries skip check).
        # Recommended: C + framework version bump as a "force invalidate all" signal for infrastructure changes.
        # If stale, warn user to re-run with force=True.

        return self._result_summary

    def save_result_summary(self) -> None:
        with open(self.summary_file, "w") as f:
            json.dump(self._result_summary.to_dict(), f, ensure_ascii=False, indent=2, sort_keys=True)

    def get_result(self, force: bool = False) -> list | dict | str | None:
        """
        Retrieves the result of the parsing operation, and run the parsing if necessary.
        Also ensures the execution status is updated, the result is saved to the output_file,
        and can be used as a cache.

        Args:
            force (bool, optional): If True, forces the parsing operation even if the output cache or file exists.
            Defaults to False.

        Returns:
            list | dict | str | None: The parsed result.

        WARNING: You may need to overwrite this method if your parser saves multiple files.
        """
        if force:
            self.save_result(force=True)
            return self._result

        if self._result is None:
            if self.output_exists():
                self._result = self._load_output()
                self.get_result_summary()
            else:
                self.save_result()

        return self._result

    def save_result(self, force: bool = False, indent=None) -> None:
        """
        Saves the result of the parsing operation to a file and returns the execution status.

        Args:
            force (bool, optional): If True, forces the parsing operation even if the output cache or file exists.
                                    Defaults to False.
            indent (int, optional): The number of spaces to use for indentation in the JSON output.
                                    Defaults to None.

        WARNING: You may need to overwrite this method if your parser saves multiple files.
        """
        if force or self._result is None or not self.output_exists():
            self._result, self._result_summary = self._execute_and_write(indent=indent)
        elif self._result_summary is None:
            self.get_result_summary()

        self.save_result_summary()

    def _execute_and_write(self, indent=None) -> tuple:
        """
        Executes the parser/analyser, writes the result to file, and builds the ResultSummary.
        Handles Generator/Iterator results for jsonl format by consuming lazily during write.
        Returns (result, summary).
        """
        # Check iOS version compatibility before executing
        if not self.is_compatible():
            logger.info(
                f"Skipping {self.module_name}: not compatible with iOS {self.case_ios_version} "
                f"(requires {self.ios_version})"
            )
            empty_result = [] if self.format == "jsonl" else {}
            summary = ResultSummary(status=ExecutionStatus.SKIPPED, num_events=0)
            self._result = empty_result
            return empty_result, summary

        handler = ResultSummaryExecutionHandler()
        handler.start()
        try:
            result = self.execute()
        except Exception as ex:
            logger.exception(f"Execution crashed: {ex}")
            handler.update(num_events=0, add_errors=1, end=True)
            self._result_summary = handler.get()
            self._result = [] if self.format == "jsonl" else {}
            return self._result, self._result_summary

        num_events = self._write_result(result, indent=indent)
        handler.update(num_events=num_events, end=True)
        return self._result, handler.get()

    def _write_result(self, result, indent=None) -> int:
        """
        Writes result to the output file and materializes it into self._result.
        For jsonl format, if result is a Generator/Iterator, it is consumed lazily.
        Returns the number of events written (only meaningful for jsonl).
        """
        num_events = 0
        with open(self.output_file, "w") as f:
            if self.format == "json":
                self._result = result
                if self.json_pretty:
                    f.write(json.dumps(self._result, ensure_ascii=False, indent=2, sort_keys=True))
                else:
                    f.write(json.dumps(self._result, ensure_ascii=False, indent=indent))
                num_events += 1
            elif self.format == "jsonl":
                # FIXME: in the future we will not materialise the entire result whenn it is a Generator/Iterator,
                # because we are defeating the purpose of using a Generator/Iterator in the first place,
                # which is to handle large data sets without consuming too much memory.
                # For now we do it to keep the contracts of get_result().
                do_materialize = isinstance(result, (Generator, Iterator))
                materialized = []
                for line in result:
                    f.write(json.dumps(line, ensure_ascii=False, indent=indent))
                    f.write("\n")
                    if do_materialize:
                        materialized.append(line)
                    num_events += 1
                self._result = materialized if do_materialize else result
            else:
                self._result = result
                f.write(self._result)
                num_events += 1
        return num_events

    def _load_output(self):
        """
        Loads the cached result from the output file.
        Returns the cached result.
        """
        with open(self.output_file) as f:
            if self.format == "json":
                return json.load(f)
            if self.format == "jsonl":
                # FIXME: In the future we should yield results lazily for jsonl format
                # instead of materializing the entire result in memory, to handle large data sets.
                return [json.loads(line) for line in f]
            else:
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
    def __init__(self, module_filename: str, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(module_filename, config, case)

    @abstractmethod
    def get_log_files(self) -> list:
        """
        Retrieves the log files used by this parser.

        Returns:
            list: A list of log files that exist.
        """
        pass


class BaseAnalyserInterface(BaseInterface):
    def __init__(self, module_filename: str, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(module_filename, config, case)


@dataclass(order=True)
class Event:
    datetime: datetime_datetime  # timestamp of the event
    message: str  # human-readable message
    module: str  # module name (e.g. "crashlogs")

    timestamp_desc: str = ""  # description of the timestamp (e.g. "sysdiagnose creation time")
    data: dict = field(default_factory=dict)  # dict with the data of the event

    # allows access to the attributes as if they were dictionary keys
    def __getitem__(self, key):
        if key == "datetime":
            # return the timestamp as a datetime str
            return self.datetime.isoformat(timespec="microseconds")
        elif key == "timestamp":  # temporary backwards compatibility
            # return the timestamp as a timestamp int
            return int(self.datetime.timestamp())
        return getattr(self, key)

    # allows access to the attributes as if they were dictionary keys
    def __setitem__(self, key, value) -> None:
        if key == "datetime":
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
        output.update(
            {
                "datetime": self.datetime.isoformat(timespec="microseconds"),
                "message": self.message,
                "timestamp_desc": self.timestamp_desc,
                "module": self.module,
                "data": self.data,
            }
        )
        return output

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """
        Populates the Event object from a dictionary.

        Args:
            data (dict): A dictionary containing the event data.
        """
        try:
            datetime = datetime_datetime.fromisoformat(data.get("datetime", ""))
        except Exception:
            try:
                datetime = datetime_datetime.fromtimestamp(data.get("timestamp", ""), tz=UTC)
            except Exception as e:
                logger.error(f"Failed to parse timestamp: {e}", exc_info=True)
                raise ValueError(
                    "Invalid timestamp format in data dictionary: no isoformat datetime or timestamp int."
                ) from e

        message = data.get("message", "")
        module = data.get("module", "")
        event = cls(datetime=datetime, message=message, module=module)
        event.timestamp_desc = data.get("timestamp_desc", "")
        event.data = data.get("data", {})
        return event
