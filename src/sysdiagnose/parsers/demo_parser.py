#! /usr/bin/env python3

import os
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger, Event
from datetime import datetime


class DemoParser(BaseParserInterface):
    description = "Demo parsers"
    format = "jsonl"  # by default json, use jsonl for event-based data

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
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
                event = Event(
                    datetime=timestamp,
                    message=f"Demo event from {log_file}",  # String with an informative message of the event
                    module=self.module_name,
                    timestamp_desc='Demo timestamp',        # String explaining what type of timestamp it is for example file created
                )

                result.append(event.to_dict())
                logger.info(f"Processing file {log_file}, new entry added", extra={'log_file': log_file})
                logger.debug(f"Entry details {str(entry)}", extra={'entry': str(entry)})
                if not entry:
                    logger.warning("Empty entry.")
                    # logger.error("Empty entry.")
            except Exception:
                logger.exception("This will log an error with the exception information")
                # logger.warning("This will log a warning with the exception information", exc_info=True)
        return result
