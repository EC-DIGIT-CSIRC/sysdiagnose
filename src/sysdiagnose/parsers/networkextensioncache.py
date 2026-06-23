#! /usr/bin/env python3
"""
For Python3
Script to extract the values from logs/Networking/com.apple.networkextension.plist
Author: Emilien Le Jamtel
"""

import glob
import os

from sysdiagnose.utils import misc
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger


class NetworkExtensionCacheParser(BaseParserInterface):
    description = "Parsing networkextensioncache plist file"

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def get_log_files(self) -> list:
        log_files_globs = ["logs/Networking/com.apple.networkextension.cache.plist"]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        log_files = self.get_log_files()
        if not log_files:
            logger.warning("No com.apple.networkextension.cache.plist file present")
            return {}
        return NetworkExtensionCacheParser.parse_file(log_files[0])

    @staticmethod
    def parse_file(path: str) -> list | dict:
        return misc.load_plist_file_as_json(path)
