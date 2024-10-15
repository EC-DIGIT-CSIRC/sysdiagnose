#! /usr/bin/env python3

# For Python3
# Script to parse system_logs.logarchive
# Author: david@autopsit.org
#
#
from collections.abc import Generator
from datetime import datetime, timezone
from sysdiagnose.utils.base import BaseParserInterface
import glob
import json
import os
import platform
import subprocess
import sys
import tempfile
import shutil
import logging

logger = logging.getLogger('sysdiagnose')
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
        log_folder_glob = '**/system_logs.logarchive/'
        return glob.glob(os.path.join(self.case_data_folder, log_folder_glob), recursive=True)

    @DeprecationWarning
    def execute(self) -> list | dict:
        # OK, this is really inefficient as we're reading all to memory, writing it to a temporary file on disk, and re-reading it again
        # but who cares, nobody uses this function anyway...
        try:
            with tempfile.TemporaryDirectory() as tmp_outpath:
                tmp_output_file = os.path.join(tmp_outpath.name, 'logarchive.tmp')
                LogarchiveParser.parse_all_to_file(self.get_log_files(), tmp_output_file)
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
            LogarchiveParser.parse_all_to_file(self.get_log_files(), self.output_file)

    def merge_files(temp_files: list, output_file: str):
        for temp_file in temp_files:
            first_entry, last_entry = LogarchiveParser.get_first_and_last_entries(temp_file['file'].name)
            temp_file['first_timestamp'] = first_entry['time']
            temp_file['last_timestamp'] = last_entry['time']

        # lowest first timestamp, second key highest last timestamp
        temp_files.sort(key=lambda x: (x['first_timestamp'], -x['last_timestamp']))

        # do the merging magic here
        # Open output file, with r+,
        # Look at next file,
        # - if current_last < prev_last: continue # skip file
        # - elif current_first  > prev_last: copy over full file, prev_last=current_last
        # - else: # need to seek to prev_last and copy over new data
        # Continue with other files with the same logic.
        prev_temp_file = temp_files[0]
        # first copy over first file to self.output_file
        shutil.copyfile(prev_temp_file['file'].name, output_file)
        with open(output_file, 'a') as f_out:
            i = 1
            while i < len(temp_files):
                current_temp_file = temp_files[i]
                if current_temp_file['last_timestamp'] < prev_temp_file['last_timestamp']:
                    # skip file as we already have all the data
                    # no need to update the prev_temp_file variable
                    pass
                elif current_temp_file['first_timestamp'] > prev_temp_file['last_timestamp']:
                    # copy over the full file
                    with open(current_temp_file['file'].name, 'r') as f_in:
                        for line in f_in:
                            f_out.write(line)
                    prev_temp_file = current_temp_file
                else:
                    # need to seek to prev_last and copy over new data
                    with open(current_temp_file['file'].name, 'r') as f_in:
                        copy_over = False   # store if we need to copy over, spares us of json.loads() every line when we know we should be continuing
                        for line in f_in:
                            if not copy_over and json.loads(line)['time'] > prev_temp_file['last_timestamp']:
                                copy_over = True
                            if copy_over:
                                f_out.write(line)
                    prev_temp_file = current_temp_file
                i += 1

    def get_first_and_last_entries(output_file: str) -> tuple:
        with open(output_file, 'rb') as f:
            first_entry = json.loads(f.readline().decode())
            # discover last line efficiently
            f.seek(-2, os.SEEK_END)  # Move the pointer to the second-to-last byte in the file
            # Move backwards until a newline character is found, or we hit the start of the file
            while f.tell() > 0:
                char = f.read(1)
                if char == b'\n':
                    break
                f.seek(-2, os.SEEK_CUR)  # Move backwards

            # Read the last line
            last_entry = json.loads(f.readline().decode())

            return (first_entry, last_entry)

    def parse_all_to_file(folders: list, output_file: str):
        # no caching
        # simple mode: only one folder
        if len(folders) == 1:
            LogarchiveParser.parse_folder_to_file(folders[0], output_file)
            return

        # complex mode: multiple folders, need to merge multiple files
        # for each of the log folders
        # - parse it to a temporary file, keep track of the file reference or name
        # - keep track of the first and last timestamp of each file
        # - order the files, and if a file contains a subset of another one, skip it.
        #   this is a though one, as we may have partially overlapping timeframes, so we may need to re-assemble in a smart way.
        # - once we know the order, bring the files together to the final single output file

        temp_files = []
        try:
            for folder in folders:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                LogarchiveParser.parse_folder_to_file(folder, temp_file.name)
                temp_files.append({
                    'file': temp_file,
                })

            # merge files to the output file
            LogarchiveParser.merge_files(temp_files, output_file)

        finally:
            # close all temp files, ensuring they are deleted
            for temp_file in temp_files:
                os.remove(temp_file['file'].name)

    def parse_folder_to_file(input_folder: str, output_file: str) -> bool:
        try:
            if (platform.system() == 'Darwin'):
                LogarchiveParser.__convert_using_native_logparser(input_folder, output_file)
            else:
                LogarchiveParser.__convert_using_unifiedlogparser(input_folder, output_file)
            return True
        except IndexError:
            logger.error('Error: No system_logs.logarchive/ folder found in logs/ directory')
            return False

    def __convert_using_native_logparser(input_folder: str, output_file: str) -> list:
        with open(output_file, 'w') as f_out:
            # output to stdout and not to a file as we need to convert the output to a unified format
            cmd_array = ['/usr/bin/log', 'show', input_folder, '--style', 'ndjson']
            # read each line, convert line by line and write the output directly to the new file
            # this approach limits memory consumption
            for line in LogarchiveParser.__execute_cmd_and_yield_result(cmd_array):
                try:
                    entry_json = LogarchiveParser.convert_entry_to_unifiedlog_format(json.loads(line))
                    f_out.write(json.dumps(entry_json) + '\n')
                except json.JSONDecodeError as e:
                    logger.warning(f"WARNING: error parsing JSON {line}: {str(e)}")
                except KeyError:
                    # last line of log does not contain 'time' field, nor the rest of the data.
                    # so just ignore it and all the rest.
                    # last line looks like {'count':xyz, 'finished':1}
                    logger.debug(f"Looks like we arrive to the end of the file: {line}")
                    break

    def __convert_using_unifiedlogparser(input_folder: str, output_file: str) -> list:
        logger.warning('WARNING: using Mandiant UnifiedLogReader to parse logs, results will be less reliable than on OS X')
        # run the conversion tool, saving to a temp folder
        # read the created file/files, add timestamp
        # sort based on time
        # save to one single file in output folder

        # first check if binary exists in PATH, if not, return an error
        try:
            subprocess.check_output(cmd_parsing_linux_test, universal_newlines=True)
        except FileNotFoundError:
            logger.error('ERROR: UnifiedLogReader not found, please install it. See README.md for more information.')
            return

        # really run the tool now
        entries = []
        with tempfile.TemporaryDirectory() as tmp_outpath:
            cmd_array = ['unifiedlog_parser_json', '--input', input_folder, '--output', tmp_outpath]
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
                            logger.warning(f"WARNING: error parsing JSON {fname_reading}: {str(e)}")
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
            timestamp = LogarchiveParser.convert_unifiedlog_time_to_datetime(entry['time'])
            entry['datetime'] = timestamp.isoformat(timespec='microseconds')
            entry['timestamp'] = timestamp.timestamp()
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
        timestamp = datetime.fromisoformat(new_entry['time'])
        new_entry['datetime'] = timestamp.isoformat(timespec='microseconds')
        new_entry['timestamp'] = timestamp.timestamp()
        new_entry['time'] = new_entry['timestamp'] * 1000000000

        return new_entry

    def convert_native_time_to_unifiedlog_format(time: str) -> int:
        timestamp = datetime.fromisoformat(time)
        return int(timestamp.timestamp() * 1000000000)

    def convert_unifiedlog_time_to_datetime(time: int) -> datetime:
        # convert time to datetime object
        timestamp = datetime.fromtimestamp(time / 1000000000, tz=timezone.utc)
        return timestamp
