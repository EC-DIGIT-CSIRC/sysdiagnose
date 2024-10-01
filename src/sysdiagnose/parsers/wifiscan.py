#! /usr/bin/env python3

import glob
import os
import re
from sysdiagnose.utils.base import BaseParserInterface


class WifiScanParser(BaseParserInterface):
    description = "Parsing wifi_scan files"

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
            output.extend(WifiScanParser.parse_file(logfile))
        return output

    def parse_file(path: str) -> list | dict:
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
                    items = line.split(',')
                    for item in items:
                        key, value = item.split('=')
                        parsed_data[key.strip()] = value.strip()
                else:
                    # extract key-value by string

                    # first ssid and ssid_hex, but need to detect the type first
                    regexes = [
                        # iOS 16 and later: FIRSTCONWIFI - ssid=4649525354434f4e57494649
                        r"(?P<ssid>.+?) - ssid=(?P<ssid_hex>[^,]+)",
                        # iOS 15: 'FIRSTCONWIFI' (4649525354434f4e57494649)
                        r"'(?P<ssid>[^\']+)' \((?P<ssid_hex>[^\)]+)\)",
                        # hidden:  <HIDDEN>
                        r"(?P<ssid><HIDDEN>)(?P<ssid_hex>)",
                    ]
                    for regex in regexes:
                        m = re.match(regex, line)
                        if m:
                            parsed_data['ssid'] = m.group('ssid')
                            parsed_data['ssid_hex'] = m.group('ssid_hex')
                            break
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
                            index_close = line.index(']', index_now)
                            value = line[index_equals + 1:index_close].strip()
                        else:
                            try:
                                index_close = line.index(',', index_now)
                            except ValueError:  # catch end of line
                                index_close = len(line)
                            value = line[index_equals + 1:index_close].strip()
                        index_now = index_close + 2
                        parsed_data[key] = value
                output.append(parsed_data)
        return output
