import json
import glob
import os
from sysdiagnose.utils.base import BaseParserInterface, logger


class TransparencyJsonParser(BaseParserInterface):

    description = "Parsing transparency.log json file as json"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'transparency.log',
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
            logger.info("No known transparency.log file found.")
            return {}
        for file in files:
            with open(file, 'r') as f:
                try:
                    return json.load(f)
                except json.decoder.JSONDecodeError:
                    logger.warning(f"Error parsing {file}")
                    return {}
