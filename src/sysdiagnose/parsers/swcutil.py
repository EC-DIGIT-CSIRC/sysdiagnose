#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

import glob
import os
from sysdiagnose.utils.base import BaseParserInterface, logger, Event
from sysdiagnose.utils.misc import snake_case
from datetime import datetime
import re


class SwcutilParser(BaseParserInterface):
    description = "Parsing swcutil_show file"
    format = 'jsonl'
    module_name = 'swcutil'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'swcutil_show.txt'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list:
        try:
            return self.parse_file(self.get_log_files()[0])
        except IndexError:
            logger.info('No swcutil_show.txt file present.')
            return []

    def parse_file(self, path: str) -> list:
        try:
            entries = []
            with open(path, 'r') as f_in:
                # init section
                headers = []
                db = []
                network = []
                settings = []
                status = 'headers'
                # stripping
                for line in f_in:
                    if line.strip() == "":
                        continue
                    if line.strip() == "=================================== DATABASE ===================================":
                        status = 'db'
                        continue
                    elif line.strip() == "=================================== NETWORK ====================================":
                        status = 'network'
                        continue
                    elif line.strip() == "=================================== SETTINGS ===================================":
                        status = 'settings'
                        continue
                    elif line.strip() == "================================= MEMORY USAGE =================================":
                        status = 'memory'
                        continue
                    elif status == 'headers':
                        headers.append(line.strip())
                        continue
                    elif status == 'db':
                        db.append(line.strip())
                        continue
                    elif status == 'network':
                        network.append(line.strip())
                        continue
                    elif status == 'settings':
                        settings.append(line.strip())
                        continue
                    elif status == 'memory':
                        entries.append(self.parse_memory_entry(line.strip()))
                        continue

                # call parsing function per section, if not done before
                entries.append(self.parse_headers_entry(headers))

                entries.extend(self.parse_db(db))
                entries.extend(self.parse_settings(settings))
                entries.extend(self.parse_network(network))

            return entries
        except IndexError:
            return []

    def parse_basic(self, data) -> dict:
        entry = {}
        for line in data:
            splitted = line.split(":", 1)
            if len(splitted) > 1:
                entry[snake_case(splitted[0])] = splitted[1].strip()
        entry['module'] = SwcutilParser.module_name
        return entry

    def parse_headers_entry(self, data) -> dict:
        entry = self.parse_basic(data)
        entry['section'] = 'headers'
        timestamp = self.sysdiagnose_creation_datetime
        event = Event(
            datetime=timestamp,
            message="swcutil headers",
            module=SwcutilParser.module_name,
            timestamp_desc='swcutil headers at sysdiagnose creation',
            data=entry
        )
        return event.to_dict()

    def parse_network(self, data) -> list:
        results = []
        timestamp = self.sysdiagnose_creation_datetime

        for line in data:
            for entry in line.split(', '):
                domain = entry.split(' ')[0]
                event = Event(
                    datetime=timestamp,
                    message=f"Network: {domain}",
                    module=SwcutilParser.module_name,
                    timestamp_desc='sysdiagnose creation time',
                    data={
                        'domain': domain,
                        'section': 'network'
                    }
                )
                results.append(event.to_dict())
        return results

    def parse_db(self, data) -> list:
        # init
        results = []
        buffer = []
        for line in data:
            if line.strip() == "--------------------------------------------------------------------------------":
                results.append(self.parse_db_entry(buffer))
                buffer = []
            else:
                buffer.append(line.strip())
        # last entry
        results.append(self.parse_db_entry(buffer))
        return results

    def parse_db_entry(self, buffer) -> dict:
        entry = self.parse_basic(buffer)
        entry['section'] = 'db'
        try:
            # iOS 18.2 changed the datetime format
            rex = re.compile(r'(\d{4}-\d{2}-\d{2}\s+)(\d):')
            normalised_ts = rex.sub(r'\g<1>0\2:', entry['last_checked'])
            timestamp = datetime.strptime(normalised_ts, '%Y-%m-%d %H:%M:%S %z')
            timestamp_desc = 'db last checked'
        except KeyError:
            timestamp = self.sysdiagnose_creation_datetime
            timestamp_desc = 'sysdiagnose creation time'
        except ValueError:
            timestamp = datetime.strptime(normalised_ts, '%Y-%m-%d %I:%M:%S %p %z')
            timestamp_desc = 'db last checked'

        event = Event(
            datetime=timestamp,
            message=f"{entry['service']}: {entry['app_id']} for {entry['domain']}",
            module=SwcutilParser.module_name,
            timestamp_desc=timestamp_desc,
            data=entry
        )
        return event.to_dict()

    def parse_settings(self, data) -> list:
        results = []
        buffer = []
        if data[0] == '(empty)':
            return []

        for line in data:
            if line.strip() == "--------------------------------------------------------------------------------":
                results.append(self.parse_settings_entry(buffer))
                buffer = []
            else:
                buffer.append(line.strip())
        # last entry
        results.append(self.parse_settings_entry(buffer))
        return results

    def parse_settings_entry(self, buffer) -> dict:
        entry = {}
        entry['section'] = 'settings'
        s = ''.join(buffer)
        '''
        { s = applinks, a = com.apple.AppStore, d = (null) }: {
            "com.apple.LaunchServices.enabled" = 1;
        }
        '''
        pattern = re.compile(r'{ s = (?P<s>[^,]+), a = (?P<a>[^,]+), d = (?P<d>[^}]+) }')
        match = pattern.search(s)
        if match:
            entry['s'] = match.group('s').strip()
            entry['a'] = match.group('a').strip()
            entry['d'] = match.group('d').strip()

        settings_pattern = re.compile(r'"(?P<key>[^"]+)" = (?P<value>[^;]+);')
        settings_matches = settings_pattern.findall(s)
        entry['settings'] = {snake_case(key): value.strip() for key, value in settings_matches}

        timestamp = self.sysdiagnose_creation_datetime
        event = Event(
            datetime=timestamp,
            message=f"swcutil settings {entry['s']} {entry['a']}",
            module=SwcutilParser.module_name,
            timestamp_desc='sysdiagnose creation time',
            data=entry
        )

        return event.to_dict()

    def parse_memory_entry(self, line):
        entry = {}
        entry['section'] = 'memory'
        timestamp = self.sysdiagnose_creation_datetime

        proc, value = line.split(":", 1)
        entry['process'] = proc.strip()
        # convert human readable bytes and KB to int
        value = value.strip()
        if 'bytes' in value or 'octets' in value:
            entry['usage'] = int(value.split(' ')[0])
        elif 'KB' in value or 'ko' in value:
            entry['usage'] = int(value.split(' ')[0]) * 1024
        elif 'MB' in value or 'mo' in value:
            entry['usage'] = int(value.split(' ')[0]) * 1024 * 1024
        elif 'GB' in value or 'go' in value:
            entry['usage'] = int(value.split(' ')[0]) * 1024 * 1024 * 1024

        message = entry['process']
        if 'usage' in entry:
            message += f" memory usage: {entry['usage']} bytes"

        event = Event(
            datetime=timestamp,
            message=message,
            module=SwcutilParser.module_name,
            timestamp_desc='memory usage at sysdiagnose creation',
            data=entry
        )
        return event.to_dict()
