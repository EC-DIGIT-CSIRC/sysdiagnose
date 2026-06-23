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


class NetworkExtensionParser(BaseParserInterface):
    description = "Parsing networkextension plist file"

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def is_compatible(self) -> bool:
        version_compatibility = super().is_compatible()
        # not compatible with Apple TV
        device_compatibility = "AppleTV" not in self.case_model and "Watch" not in self.case_model
        # both need to be compatible
        return version_compatibility and device_compatibility

    def get_log_files(self) -> list:
        log_files_globs = ["logs/Networking/com.apple.networkextension.plist"]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        for log_file in self.get_log_files():
            return NetworkExtensionParser.parse_file(log_file)
        logger.warning("No com.apple.networkextension.plist file present")
        return {}

    @staticmethod
    def parse_file(path: str) -> list | dict:
        return misc.load_plist_file_as_json(path)
