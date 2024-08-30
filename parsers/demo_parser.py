#! /usr/bin/env python3

import os
import json
from utils.base import BaseParserInterface


class DemoParser(BaseParserInterface):
    description = "Demo parsers"
    # format = "json"  # by default json

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files = [
            "demo_input_file.txt"
        ]
        return [os.path.join(self.case_data_subfolder, log_files) for log_files in log_files]

    def execute(self) -> list | dict:
        '''
        this is the function that will be called
        '''
        json_object = {}
        log_files = self.get_log_files()
        for log_file in log_files:
            pass
        return json_object

    def parse_path_to_folder(self, path: str, output_folder: str) -> bool:
        '''
        this is the function that will be called
        '''
        try:
            json_object = {}
            log_files = self.get_log_files(path)
            for log_file in log_files:
                pass
            # ideally stream to the file directly
            output_folder = os.path.join(output_folder, __name__.split('.')[-1])
            os.makedirs(output_folder, exist_ok=True)
            with open(os.path.join(output_folder, "demo_output.json"), "w") as f:
                json.dump(json_object, f)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
