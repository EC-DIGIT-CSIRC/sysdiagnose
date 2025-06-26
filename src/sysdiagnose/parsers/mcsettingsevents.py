#! /usr/bin/env python3

import glob
import os
from sysdiagnose.utils.base import BaseParserInterface, Event
import sysdiagnose.utils.misc as misc
from datetime import datetime, timezone


class McSettingsEventsParser(BaseParserInterface):
    description = "Parsing MC Settings Events plist file"
    format = "jsonl"  # by default json

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            "logs/MCState/Shared/MCSettingsEvents.plist"
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            for item in glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)):
                if os.path.getsize(item) > 0:
                    log_files.append(item)
        return log_files

    def execute(self) -> list | dict:
        '''
        this is the function that will be called
        '''
        result = []
        log_files = self.get_log_files()
        for log_file in log_files:
            json_data = misc.load_plist_file_as_json(log_file)
            for entry in McSettingsEventsParser.traverse_and_collect(data=json_data, module=self.module_name):
                result.append(entry)

        return result

    def traverse_and_collect(data, module, path=""):
        '''
        recursively traverse json_data and search for dicts that contain the 'timestamp' key.
        when found, convert the value of the 'timestamp' key to a datetime object and add it to the entry dict.
        also add a field 'setting' with the path of the dict in the json_data where the 'timestamp' key was found. (each depth joined by a dot)
        '''
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if 'timestamp' in value:
                try:
                    timestamp = datetime.strptime(value['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
                    timestamp = timestamp.replace(tzinfo=timezone.utc)  # ensure timezone is UTC
                    value.pop('timestamp')  # remove timestamp from value to avoid duplication
                    event = Event(
                        datetime=timestamp,
                        message=f"setting {current_path} {value['event']} by {value['process']}",
                        module=module,
                        timestamp_desc=f"{module} {value['event']}",
                        data=value
                    )
                    event.data['setting'] = current_path

                    yield event.to_dict()
                except ValueError:
                    pass
            elif isinstance(value, dict):
                for event in McSettingsEventsParser.traverse_and_collect(data=value, module=module, path=current_path):
                    yield event
