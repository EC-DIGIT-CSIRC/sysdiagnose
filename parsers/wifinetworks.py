#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

import json
import glob
import utils.misc as misc
import os
from utils.base import BaseParserInterface


class WifiNetworksParser(BaseParserInterface):

    description = "Parsing com.apple.wifi plist files"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'WiFi/*.plist',
            'WiFi/com.apple.wifi.recent-networks.json'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> dict:
        result = {}
        for logfile in self.get_log_files():
            end_of_path = os.path.splitext(os.path.basename(logfile))[0]  # keep the filename without the extension
            result[end_of_path] = WifiNetworksParser.parse_file(logfile)
        return result

    def parse_file(fname: str) -> dict | list:
        if fname.endswith('.json'):
            with open(fname, 'r') as f:
                return json.load(f)
        if fname.endswith('.plist'):
            return misc.load_plist_file_as_json(fname)
