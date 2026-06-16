import glob
import json
import os

from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger


class TransparencyJsonParser(BaseParserInterface):
    description = "Parsing transparency.log json file as json"
    ios_version = ">=16.0"

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def is_compatible(self) -> bool:
        version_compatibility = super().is_compatible()
        # not compatible with Apple TV
        device_compatibility = "AppleTV" not in self.case_model and "Watch" not in self.case_model
        # both need to be compatible
        return version_compatibility and device_compatibility

    def get_log_files(self) -> list:
        log_files_globs = [
            "transparency.log",
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            for item in glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)):
                if os.path.getsize(item) > 0:
                    log_files.append(item)

        return log_files

    def execute(self) -> dict:
        files = self.get_log_files()
        if not files:
            logger.warning("No known transparency.log file found.")
            return {}
        for file in files:
            with open(file) as f:
                try:
                    return json.load(f)
                except json.decoder.JSONDecodeError:
                    logger.warning(f"Error parsing {file}")
                    return {}
