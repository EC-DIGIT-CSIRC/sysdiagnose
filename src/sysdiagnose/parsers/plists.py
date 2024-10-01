#! /usr/bin/env python3

import glob
import sysdiagnose.utils.misc as misc
import os
import json
from sysdiagnose.utils.base import BaseParserInterface


class PlistParser(BaseParserInterface):
    description = "Parsing any pslist into json"

    def __init__(self, config: dict, case_id: str):
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

    def save_result(self, force: bool = False, indent=None):
        """
        Saves the result of the parsing operation to many files in the parser output folder

        This function overrides the default save_result function to save each file in a different json file
        """
        os.makedirs(self.output_folder, exist_ok=True)
        if not force and self._result is not None:
            # the result was already computed
            for end_of_path, json_data in self._result.items():
                output_filename = end_of_path.replace(os.path.sep, '_') + '.json'  # replace / with _ in the path
                with open(os.path.join(self.output_folder, output_filename), 'w') as f:
                    f.write(json.dumps(json_data, ensure_ascii=False))
        else:
            # no caching
            for logfile in self.get_log_files():
                try:
                    json_data = misc.load_plist_file_as_json(logfile)
                except Exception as e:
                    json_data = {"error": str(e)}
                end_of_path = logfile[len(self.case_data_subfolder):].lstrip(os.path.sep)   # take the path after the root path
                output_filename = end_of_path.replace(os.path.sep, '_') + '.json'  # replace / with _ in the path
                with open(os.path.join(self.output_folder, output_filename), 'w') as f:
                    f.write(json.dumps(json_data, ensure_ascii=False))
