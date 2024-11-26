#! /usr/bin/env python3

import glob
import os
import re
from sysdiagnose.utils.base import BaseParserInterface, logger


class WifiScanParser(BaseParserInterface):
    description = "Parsing wifi_scan files"
    format = "jsonl"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'WiFi/wifi_scan*.txt'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        output = []
        for logfile in self.get_log_files():
            output.extend(self.parse_file(logfile))
        return output

    def parse_file(self, path: str) -> list | dict:
        output = []
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                # skip empty lines
                if not line:
                    continue
                parsed_data = {}
                # process header
                if line.startswith('total='):
                    parsed_data.update(WifiScanParser.parse_summary(line))
                else:
                    # extract key-value by string
                    parsed_data.update(WifiScanParser.parse_line(line))

                timestamp = self.sysdiagnose_creation_datetime
                parsed_data['datetime'] = timestamp.isoformat(timespec='microseconds')
                parsed_data['timestamp'] = timestamp.timestamp()
                output.append(parsed_data)
        return output

    def parse_summary(line: str) -> dict:
        parsed = {}
        items = line.split(',')
        for item in items:
            key, value = item.split('=')
            parsed[key.strip()] = value.strip()
        return parsed

    def parse_line(line: str) -> dict:
        parsed = {}
        # first ssid and ssid_hex, but need to detect the type first
        regexes = [
            # iOS 16 and later: FIRSTCONWIFI - ssid=4649525354434f4e57494649
            r"(?P<ssid>.+?) - ssid=(?P<ssid_hex>[^,]+)",
            # iOS 15: 'FIRSTCONWIFI' (4649525354434f4e57494649)
            r"'(?P<ssid>[^\']+)' \((?P<ssid_hex>[^\)]+)\)",
            # iOS ??: 'FIRSTCONWIFI' <46495253 54434f4e 57494649>
            r"'(?P<ssid>[^\']+)' \<(?P<ssid_hex>[^>]+)\>",
            # hidden:  <HIDDEN>
            r"(?P<ssid><HIDDEN>)(?P<ssid_hex>)",
        ]
        for regex in regexes:
            m = re.match(regex, line)
            if m:
                parsed['ssid'] = m.group('ssid')
                parsed['ssid_hex'] = m.group('ssid_hex').replace(' ', '')
                break
        if 'ssid' not in parsed:
            parsed['ssid'] = '<unknown>'
            logger.warning(f"Failed to parse ssid from line: {line}")
        # key = first place with =
        #  check what is after =, if normal char then value is until next ,
        #                         if [ then value is until ]
        #                         if { then value is until }
        index_now = line.index(',') + 1
        # now the rest of the line
        while index_now < len(line):
            index_equals = line.index('=', index_now)
            key = line[index_now:index_equals].strip()
            if line[index_equals + 1] in ['[']:
                try:
                    index_close = line.index(']', index_now)
                except Exception:
                    index_close = len(line)  # no ending found
                value = line[index_equals + 2:index_close].strip()
            else:
                try:
                    index_close = line.index(',', index_now)
                except ValueError:  # catch end of line
                    index_close = len(line)
                value = line[index_equals + 1:index_close].strip()
            index_now = index_close + 2
            parsed[key] = value

        return parsed
