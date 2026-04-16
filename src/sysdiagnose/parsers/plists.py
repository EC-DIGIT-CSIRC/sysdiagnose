#! /usr/bin/env python3

import glob
import json
import os

from sysdiagnose.utils import misc
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig


class PlistParser(BaseParserInterface):
    description = "Parsing any pslist into json"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)
        self.output_folder = os.path.join(self.case_parsed_data_folder, self.module_name)

    def get_log_files(self) -> list:
        log_files_globs = [
            '**/*.plist'
        ]
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
            end_of_path = logfile[len(self.case_data_subfolder):].lstrip(os.path.sep)  # take the path after the root path
            result[end_of_path] = json_data
        return result

    # LATER output_exists() now always returns False. This is because the output is saved in multiple files.
    # we may want to change this behavior in the future, but that requires overwriting output_exists() and get_result() here

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
        if force or self._result is None:
            self._result = self.execute_with_result_summary()
        elif self._result_summary is None:
            self._result_summary = self.load_result_summary()

        for end_of_path, json_data in self._result.items():
            output_filename = end_of_path.replace(os.path.sep, '_') + '.json'  # replace / with _ in the path
            with open(os.path.join(self.output_folder, output_filename), 'w') as f:
                f.write(json.dumps(json_data, ensure_ascii=False))

        self.save_result_summary()
