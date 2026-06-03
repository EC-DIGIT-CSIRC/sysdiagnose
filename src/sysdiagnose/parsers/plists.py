#! /usr/bin/env python3

import glob
import json
import os

from sysdiagnose.utils import misc
from sysdiagnose.utils.base import (
    BaseParserInterface,
    SysdiagnoseConfig,
)


class PlistParser(BaseParserInterface):
    description = "Parsing any pslist into json"

    def __init__(self, config: SysdiagnoseConfig, case_id: str) -> None:
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

    @staticmethod
    def parse_file(file_path: str) -> dict:
        try:
            return misc.load_plist_file_as_json(file_path)
        except Exception as e:
            return {"error": str(e)}

    def _write_result(self, result, indent=None) -> int:
        self._result = result
        os.makedirs(self.output_folder, exist_ok=True)

        for filename in os.listdir(self.output_folder):
            if filename.endswith(".json"):
                os.remove(os.path.join(self.output_folder, filename))

        for end_of_path, json_data in self._result.items():
            output_filename = end_of_path.replace(os.path.sep, "_") + ".json"
            with open(os.path.join(self.output_folder, output_filename), "w") as f:
                f.write(json.dumps(json_data, ensure_ascii=False))

        return len(self._result)

    def _load_output(self) -> dict:
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
