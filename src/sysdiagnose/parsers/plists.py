#! /usr/bin/env python3

import glob
import json
import os
from datetime import UTC, datetime

from sysdiagnose.utils import misc
from sysdiagnose.utils.base import (
    BaseParserInterface,
    ExecutionStatus,
    ResultSummary,
    ResultSummaryFactory,
    ResultSummaryLogHandler,
    SysdiagnoseConfig,
    logger,
)


class PlistParser(BaseParserInterface):
    description = "Parsing any pslist into json"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)
        self.output_folder = os.path.join(self.case_parsed_data_folder, self.module_name)

    def get_log_files(self) -> list:
        log_files_globs = ["**/*.plist"]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob), recursive=True))

        return log_files

    def execute(self) -> dict:
        result = {}
        for logfile in self.get_log_files():
            try:
                json_data = misc.load_plist_file_as_json(logfile)
            except Exception as e:
                json_data = {"error": str(e)}
            end_of_path = logfile[len(self.case_data_subfolder) :].lstrip(os.path.sep)  # take the path after the root path
            result[end_of_path] = json_data
        return result

    def output_exists(self) -> bool:
        if not os.path.isdir(self.output_folder):
            return False

        return any(
            filename.endswith(".json") and os.path.getsize(os.path.join(self.output_folder, filename)) > 0
            for filename in os.listdir(self.output_folder)
        )

    def get_result(self, force: bool = False) -> dict:
        if force:
            self.save_result(force)
            return self._result

        if self._result is None:
            if self.output_exists():
                self._result = self._load_cached_result()
                self._result_summary = self.load_result_summary()
            else:
                self.save_result()

        return self._result

    @staticmethod
    def parse_file(file_path: str) -> dict:
        try:
            return misc.load_plist_file_as_json(file_path)
        except Exception as e:
            return {"error": str(e)}

    def save_result(self, force: bool = False, indent=None):
        """
        Saves the result of the parsing operation to many files in the parser output folder

        This function overrides the default save_result function to save each file in a different json file
        """
        os.makedirs(self.output_folder, exist_ok=True)
        if force or self._result is None or not self.output_exists():
            self._result = self.execute_with_result_summary()
        elif self._result_summary is None:
            self._result_summary = self.load_result_summary()

        for filename in os.listdir(self.output_folder):
            if filename.endswith(".json"):
                os.remove(os.path.join(self.output_folder, filename))

        for end_of_path, json_data in self._result.items():
            output_filename = end_of_path.replace(os.path.sep, "_") + ".json"  # replace / with _ in the path
            with open(os.path.join(self.output_folder, output_filename), "w") as f:
                f.write(json.dumps(json_data, ensure_ascii=False))

        self.save_result_summary()

    def execute_with_result_summary(self) -> list | dict | str | None:
        log_handler = ResultSummaryLogHandler()
        start_time = datetime.now(UTC)
        logger.addHandler(log_handler)
        try:
            result = self.execute()
        except Exception:
            duration = (datetime.now(UTC) - start_time).total_seconds()
            self._result_summary = ResultSummary(
                status=ExecutionStatus.ERROR,
                start_time=start_time,
                duration=duration,
                num_errors=max(1, log_handler.num_errors),
                num_warnings=log_handler.num_warnings,
                num_events=0,
            )
            raise
        finally:
            logger.removeHandler(log_handler)

        summary = ResultSummaryFactory.from_result(result)
        summary.start_time = start_time
        summary.duration = (datetime.now(UTC) - start_time).total_seconds()
        summary.num_errors += log_handler.num_errors
        summary.num_warnings += log_handler.num_warnings
        # In this case, we are interested in the number of files parsed.
        summary.num_events = len(result) if result else 0
        summary.status = ResultSummaryFactory.get_execution_status(summary.num_errors, summary.num_warnings)
        self._result_summary = summary
        return result

    def _load_cached_result(self) -> dict:
        result = {}
        for logfile in self.get_log_files():
            end_of_path = logfile[len(self.case_data_subfolder) :].lstrip(os.path.sep)
            output_filename = end_of_path.replace(os.path.sep, "_") + ".json"
            output_path = os.path.join(self.output_folder, output_filename)
            if not os.path.exists(output_path):
                continue

            with open(output_path) as f:
                result[end_of_path] = json.load(f)

        return result
