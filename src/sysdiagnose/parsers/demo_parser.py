#! /usr/bin/env python3

import os
from sysdiagnose.utils.base import BaseParserInterface, logger
from datetime import datetime


class DemoParser(BaseParserInterface):
    description = "Demo parsers"
    format = "jsonl"  # by default json, use jsonl for event-based data

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
        result = []
        log_files = self.get_log_files()
        for log_file in log_files:
            entry = {}
            try:
                timestamp = datetime.strptime('1980-01-01 12:34:56.001 +00:00', '%Y-%m-%d %H:%M:%S.%f %z')  # moment of interest
                entry['datetime'] = timestamp.isoformat(timespec='microseconds')
                entry['timestamp'] = timestamp.timestamp()
                entry['timestamp_desc'] = 'Demo timestamp'          # String explaining what type of timestamp it is for example file created
                entry['message'] = f"Demo message from {log_file}"  # String with an informative message of the event
                entry['saf_module'] = self.module_name

                result.append(entry)
                logger.info(f"Processing file {log_file}, new entry added", extra={'log_file': log_file})
                logger.debug(f"Entry details {str(entry)}", extra={'entry': str(entry)})
                if not entry:
                    logger.warning("Empty entry.")
                    # logger.error("Empty entry.")
            except Exception:
                logger.exception("This will log an error with the exception information")
                # logger.warning("This will log a warning with the exception information", exc_info=True)
        return result
