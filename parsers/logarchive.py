#! /usr/bin/env python3

# For Python3
# Script to parse system_logs.logarchive
# Author: david@autopsit.org
#
#
import os
import sys
import json
import tempfile
import platform
import subprocess
from datetime import datetime, timezone
from collections.abc import Generator
from utils.base import BaseParserInterface


# --------------------------------------------#

# On 2023-04-13: using ndjson instead of json to avoid parsing issues.
# Based on manpage:
#       json      JSON output.  Event data is synthesized as an array of JSON dictionaries.
#
#       ndjson    Line-delimited JSON output.  Event data is synthesized as JSON dictionaries, each emitted on a single line.
#                 A trailing record, identified by the inclusion of a 'finished' field, is emitted to indicate the end of events.
#
# cmd_parsing_osx = '/usr/bin/log show %s --style ndjson'  # fastest and short version
# cmd_parsing_osx = '/usr/bin/log show %s --style json' # fastest and short version
# cmd_parsing_osx = '/usr/bin/log show %s --info --style json' # to enable debug, add --debug
# cmd_parsing_osx = '/usr/bin/log show %s --info --debug --style json'

# Linux parsing relies on UnifiedLogReader:
#       https://github.com/mandiant/macos-UnifiedLogs
# Follow instruction in the README.md in order to install it.
# TODO unifiedlog_parser is single threaded, either patch their code for multithreading support or do the magic here by parsing each file in a separate thread
# cmd_parsing_linux = 'unifiedlog_parser_json --input %s --output %s'
cmd_parsing_linux_test = ['unifiedlog_parser_json', '--help']
# --------------------------------------------------------------------------- #

# LATER consider refactoring using yield to lower memory consumption


class LogarchiveParser(BaseParserInterface):
    description = 'Parsing system_logs.logarchive folder'
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_folders = [
            'system_logs.logarchive/'
        ]
        return [os.path.join(self.case_data_subfolder, log_folder) for log_folder in log_folders]

    @DeprecationWarning
    def execute(self) -> list | dict:
        # OK, this is really inefficient as we're reading a file that we just wrote to a temporary folder
        # but who cares, nobody uses this function anyway...
        try:
            with tempfile.TemporaryDirectory() as tmp_outpath:
                tmp_output_file = os.path.join(tmp_outpath.name, 'logarchive.tmp')
                LogarchiveParser.parse_file_to_file(self.get_log_files()[0], tmp_output_file)
                with open(tmp_output_file, 'r') as f:
                    return [json.loads(line) for line in f]
        except IndexError:
            return {'error': 'No system_logs.logarchive/ folder found in logs/ directory'}

    def get_result(self, force: bool = False):
        if force:
            # force parsing
            self.save_result(force)

        if not self._result:
            if not self.output_exists():
                self.save_result()

            if self.output_exists():
                # load existing output
                with open(self.output_file, 'r') as f:
                    for line in f:
                        try:
                            yield json.loads(line)
                        except json.decoder.JSONDecodeError:  # last lines of the native logarchive.jsonl file
                            continue
        else:
            # should never happen, as we never keep it in memory
            for entry in self._result:
                yield entry

    def save_result(self, force: bool = False, indent=None):
        '''
            Save the result of the parsing operation to a file in the parser output folder
        '''
        if not force and self._result is not None:
            # the result was already computed, just save it now
            super().save_result(force, indent)
        else:
            # no caching
            LogarchiveParser.parse_file_to_file(self.get_log_files()[0], self.output_file)

    def parse_file_to_file(input_file: str, output_file: str) -> bool:
        try:
            if (platform.system() == 'Darwin'):
                LogarchiveParser.__convert_using_native_logparser(input_file, output_file)
            else:
                LogarchiveParser.__convert_using_unifiedlogparser(input_file, output_file)
            return True
        except IndexError:
            print('Error: No system_logs.logarchive/ folder found in logs/ directory')
            return False

    def __convert_using_native_logparser(input_file: str, output_file: str) -> list:
        with open(output_file, 'w') as f_out:
            # output to stdout and not to a file as we need to convert the output to a unified format
            cmd_array = ['/usr/bin/log', 'show', input_file, '--style', 'ndjson']
            # read each line, convert line by line and write the output directly to the new file
            # this approach limits memory consumption
            for line in LogarchiveParser.__execute_cmd_and_yield_result(cmd_array):
                try:
                    entry_json = LogarchiveParser.convert_entry_to_unifiedlog_format(json.loads(line))
                    f_out.write(json.dumps(entry_json) + '\n')
                except json.JSONDecodeError as e:
                    print(f"WARNING: error parsing JSON {line}: {str(e)}")
                except KeyError:
                    # last line of log does not contain 'time' field, nor the rest of the data.
                    # so just ignore it
                    pass

    def __convert_using_unifiedlogparser(input_file: str, output_file: str) -> list:
        print('WARNING: using Mandiant UnifiedLogReader to parse logs, results will be less reliable than on OS X')
        # run the conversion tool, saving to a temp folder
        # read the created file/files, add timestamp
        # sort based on time
        # save to one single file in output folder

        # first check if binary exists in PATH, if not, return an error
        try:
            subprocess.check_output(cmd_parsing_linux_test, universal_newlines=True)
        except FileNotFoundError:
            print('ERROR: UnifiedLogReader not found, please install it. See README.md for more information.')
            return

        # really run the tool now
        entries = []
        with tempfile.TemporaryDirectory() as tmp_outpath:
            cmd_array = ['unifiedlog_parser_json', '--input', input_file, '--output', tmp_outpath]
            # run the command and get the result in our tmp_outpath folder
            LogarchiveParser.__execute_cmd_and_get_result(cmd_array)
            # read each file, conver line by line and write the output directly to the new file
            # LATER run this in multiprocessing, one per file to speed up the process
            for fname_reading in os.listdir(tmp_outpath):
                with open(os.path.join(tmp_outpath, fname_reading), 'r') as f:
                    for line in f:  # jsonl format - one json object per line
                        try:
                            entry_json = LogarchiveParser.convert_entry_to_unifiedlog_format(json.loads(line))
                            entries.append(entry_json)
                        except json.JSONDecodeError as e:
                            print(f"WARNING: error parsing JSON {fname_reading}: {str(e)}")
        # tempfolder is cleaned automatically after the block

        # sort the data as it's not sorted by default, and we need sorted data for other analysers
        entries.sort(key=lambda x: x['time'])
        # save to file as JSONL
        with open(output_file, 'w') as f_out:
            for entry in entries:
                f_out.write(json.dumps(entry))
                f_out.write('\n')

    def __execute_cmd_and_yield_result(cmd_array: list) -> Generator[dict, None, None]:
        '''
            Return None if it failed or the result otherwise.

        '''
        with subprocess.Popen(cmd_array, stdout=subprocess.PIPE, universal_newlines=True) as process:
            for line in iter(process.stdout.readline, ''):
                yield line

    def __execute_cmd_and_get_result(cmd_array: list, outputfile=None):
        '''
            Return None if it failed or the result otherwise.

            Outfile can have 3 values:
                - None: no output except return value
                - sys.stdout: print to stdout
                - path to a file to write to
        '''
        result = []

        with subprocess.Popen(cmd_array, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True) as process:
            if outputfile is None:
                for line in iter(process.stdout.readline, ''):
                    try:
                        result.append(json.loads(line))
                    except Exception:
                        result.append(line)
            elif outputfile == sys.stdout:
                for line in iter(process.stdout.readline, ''):
                    print(line)
            else:
                with open(outputfile, 'w') as outfd:
                    for line in iter(process.stdout.readline, ''):
                        outfd.write(line)
                    result = f'Output written to {outputfile}'

        return result

    def convert_entry_to_unifiedlog_format(entry: dict) -> dict:
        '''
            Convert the entry to unifiedlog format
        '''
        # already in the Mandiant unifiedlog format
        if 'event_type' in entry:
            entry['datetime'] = LogarchiveParser.convert_unifiedlog_time_to_datetime(entry['time']).isoformat()
            return entry
        '''
        jq '. |= keys' logarchive-native.json > native_keys.txt
        sort native_keys.txt | uniq -c | sort -n > native_keys_sort_unique.txt
        '''

        mapper = {
            'creatorActivityID': 'activity_id',
            'messageType': 'log_type',
            # 'source': '',   # not present in the Mandiant format
            # 'backtrace': '',  # sub-dictionary
            'activityIdentifier': 'activity_id',
            'bootUUID': 'boot_uuid',   # remove - in the UUID
            'category': 'category',
            'eventMessage': 'message',
            'eventType': 'event_type',
            'formatString': 'raw_message',
            # 'machTimestamp': '',   # not present in the Mandiant format
            # 'parentActivityIdentifier': '',  # not present in the Mandiant format
            'processID': 'pid',
            'processImagePath': 'process',
            'processImageUUID': 'process_uuid',  # remove - in the UUID
            'senderImagePath': 'library',
            'senderImageUUID': 'library_uuid',   # remove - in the UUID
            # 'senderProgramCounter': '',  # not present in the Mandiant format
            'subsystem': 'subsystem',
            'threadID': 'thread_id',
            'timestamp': 'time',  # requires conversion
            'timezoneName': 'timezone_name',  # ignore timezone as time and timestamp are correct
            # 'traceID': '',  # not present in the Mandiant format
            'userID': 'euid'
        }

        new_entry = {}
        for key, value in entry.items():
            if key in mapper:
                new_key = mapper[key]
                if 'uuid' in new_key:  # remove - in UUID
                    new_entry[new_key] = value.replace('-', '')
                else:
                    new_entry[new_key] = value
            else:
                # keep the non-matching entries
                new_entry[key] = value
        # convert time
        new_entry['datetime'] = new_entry['time']
        new_entry['time'] = LogarchiveParser.convert_native_time_to_unifiedlog_format(new_entry['time'])

        return new_entry

    def convert_native_time_to_unifiedlog_format(time: str) -> int:
        timestamp = datetime.fromisoformat(time)
        return int(timestamp.timestamp() * 1000000000)

    def convert_unifiedlog_time_to_datetime(time: int) -> datetime:
        # convert time to datetime object
        timestamp = datetime.fromtimestamp(time / 1000000000, tz=timezone.utc)
        return timestamp
