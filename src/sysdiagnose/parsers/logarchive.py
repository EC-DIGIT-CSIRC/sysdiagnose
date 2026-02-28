#! /usr/bin/env python3

# For Python3
# Script to parse system_logs.logarchive
# Author: david@autopsit.org
#
#
from collections.abc import Generator
from datetime import datetime, timezone
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger, Event
import glob
import orjson
import os
import platform
import subprocess
import sys
import tempfile
import shutil
import threading

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
cmd_parsing_linux_test = ['unifiedlog_iterator', '--help']
# --------------------------------------------------------------------------- #

# LATER consider refactoring using yield to lower memory consumption


def log_stderr(process, logger):
    """
    Reads the stderr of a subprocess and logs it line by line.
    """
    for line in iter(process.stderr.readline, b''):
        logger.debug(line.decode('utf-8', errors='replace').strip())


class LogarchiveParser(BaseParserInterface):
    description = 'Parsing system_logs.logarchive folder'
    format = 'jsonl'

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
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
                with open(tmp_output_file, 'rb') as f:
                    return [orjson.loads(line) for line in f]
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
                with open(self.output_file, 'rb') as f:
                    for line in f:
                        try:
                            yield orjson.loads(line)
                        except orjson.JSONDecodeError:  # last lines of the native logarchive.jsonl file
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
        with open(output_file, 'ab') as f_out:
            i = 1
            while i < len(temp_files):
                current_temp_file = temp_files[i]
                if current_temp_file['last_timestamp'] < prev_temp_file['last_timestamp']:
                    # skip file as we already have all the data
                    # no need to update the prev_temp_file variable
                    pass
                elif current_temp_file['first_timestamp'] > prev_temp_file['last_timestamp']:
                    # copy over the full file
                    with open(current_temp_file['file'].name, 'rb') as f_in:
                        for line in f_in:
                            f_out.write(line)
                    prev_temp_file = current_temp_file
                else:
                    # need to seek to prev_last and copy over new data
                    with open(current_temp_file['file'].name, 'rb') as f_in:
                        copy_over = False   # store if we need to copy over, spares us of orjson.loads() every line when we know we should be continuing
                        for line in f_in:
                            if not copy_over and orjson.loads(line)['time'] > prev_temp_file['last_timestamp']:
                                copy_over = True
                            if copy_over:
                                f_out.write(line)
                    prev_temp_file = current_temp_file
                i += 1

    def get_first_and_last_entries(output_file: str) -> tuple:
        with open(output_file, 'rb') as f:
            first_entry = orjson.loads(f.readline())
            # discover last line efficiently
            f.seek(-2, os.SEEK_END)  # Move the pointer to the second-to-last byte in the file
            # Move backwards until a newline character is found, or we hit the start of the file
            while f.tell() > 0:
                char = f.read(1)
                if char == b'\n':
                    break
                f.seek(-2, os.SEEK_CUR)  # Move backwards

            # Read the last line
            last_entry = orjson.loads(f.readline())

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
            # ALWAYS use unifiedlog_iterator (fast Rust binary) instead of native macOS log parser
            # The Rust binary is 10x faster and produces consistent output across platforms
            LogarchiveParser.__convert_using_unifiedlogparser(input_folder, output_file)
            return True
        except IndexError:
            logger.exception('Error: No system_logs.logarchive/ folder found in logs/ directory')
            return False
        except FileNotFoundError:
            logger.exception('Error: unifiedlogs command not found, please refer to the README for further instructions')
            return False

    def __convert_using_native_logparser(input_folder: str, output_file: str) -> list:
        with open(output_file, 'wb') as f_out:
            # output to stdout and not to a file as we need to convert the output to a unified format
            cmd_array = ['/usr/bin/log', 'show', input_folder, '--style', 'ndjson', '--info', '--debug', '--signpost']
            # read each line, convert line by line and write the output directly to the new file
            # this approach limits memory consumption
            for line in LogarchiveParser.__execute_cmd_and_yield_result(cmd_array):
                try:
                    entry_json = LogarchiveParser.convert_entry_to_unifiedlog_format(orjson.loads(line))
                    f_out.write(orjson.dumps(entry_json))
                    f_out.write(b'\n')
                except orjson.JSONDecodeError as e:
                    logger.warning(f"WARNING: error parsing JSON {line} - {e}", exc_info=True)
                except KeyError:
                    # last line of log does not contain 'time' field, nor the rest of the data.
                    # so just ignore it and all the rest.
                    # last line looks like {'count':xyz, 'finished':1}
                    logger.debug(f"Looks like we arrive to the end of the file: {line}")
                    break

    def __convert_using_unifiedlogparser(input_folder: str, output_file: str) -> list:
        """
        Let Rust write the file directly, then convert to Event format.
        unifiedlog_iterator outputs raw unifiedlog format, so we need to convert it.
        """
        # Use a temporary file for unifiedlog_iterator output
        temp_output = output_file + '.tmp'
        cmd_array = [
            'unifiedlog_iterator',
            '--mode', 'log-archive',
            '--input', input_folder,
            '--output', temp_output,
            '--format', 'jsonl'
        ]

        logger.info(f'Running: {" ".join(cmd_array)}')

        result = subprocess.run(cmd_array, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f'unifiedlog_iterator failed with code {result.returncode}')
            logger.error(f'stderr: {result.stderr}')
            raise RuntimeError(f'unifiedlog_iterator failed: {result.stderr}')

        # Convert unifiedlog format to Event format
        logger.info(f'Converting unifiedlog format to Event format')
        try:
            with open(temp_output, 'rb') as f_in, open(output_file, 'wb') as f_out:
                for line in f_in:
                    try:
                        entry = orjson.loads(line)
                        if 'event_type' in entry and 'data' not in entry:
                            converted_entry = LogarchiveParser.convert_entry_to_unifiedlog_format(entry)
                            f_out.write(orjson.dumps(converted_entry))
                            f_out.write(b'\n')
                        else:
                            f_out.write(line)
                    except orjson.JSONDecodeError:
                        continue
        finally:
            if os.path.exists(temp_output):
                os.remove(temp_output)
        logger.info(f'Successfully wrote {output_file}')
        return []

    def __convert_using_unifiedlogparser_generator(input_folder: str):
        """
        Generator that streams entries from Rust binary and converts to Event format.
        Used for cases where we need to process entries one by one.
        """
        cmd_array = [
            'unifiedlog_iterator',
            '--mode', 'log-archive',
            '--input', input_folder,
            '--format', 'jsonl'
        ]

        for line in LogarchiveParser.__execute_cmd_and_yield_result(cmd_array):
            try:
                entry_json = orjson.loads(line)
                # Convert unifiedlog format to Event format if needed
                if 'event_type' in entry_json and 'data' not in entry_json:
                    entry_json = LogarchiveParser.convert_entry_to_unifiedlog_format(entry_json)
                yield entry_json
            except orjson.JSONDecodeError:
                pass

    def __execute_cmd_and_yield_result(cmd_array: list) -> Generator[str, None, None]:
        '''
            Return None if it failed or the result otherwise.
            Uses buffered reading for better performance.

            Chunk size of 1MB provides optimal balance between:
            - Reducing system call overhead (fewer read() calls)
            - Memory efficiency (not too large)
            - Pipe buffer utilization (macOS pipes are typically 64KB-512KB)
        '''
        CHUNK_SIZE = 1024 * 1024  # 1MB chunks for optimal throughput
        BUFFER_SIZE = 2 * 1024 * 1024  # 2MB subprocess buffer

        with subprocess.Popen(cmd_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=False, bufsize=BUFFER_SIZE) as process:
            # start a thread to log stderr
            stderr_thread = threading.Thread(target=log_stderr, args=(process, logger), daemon=True)
            stderr_thread.start()

            # Use buffered reading for better performance
            buffer = b''
            while True:
                chunk = process.stdout.read(CHUNK_SIZE)
                if not chunk:
                    break
                buffer += chunk

                # Process complete lines
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if line:  # Skip empty lines
                        yield line.decode('utf-8')

            # Process any remaining data in buffer
            if buffer:
                yield buffer.decode('utf-8')

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
                        result.append(orjson.loads(line))
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

        timestamp_desc = 'logarchive'
        module = 'logarchive'

        # already in the Mandiant unifiedlog format
        if 'event_type' in entry:
            timestamp = LogarchiveParser.convert_unifiedlog_time_to_datetime(entry['time'])
            entry['datetime'] = timestamp.isoformat(timespec='microseconds')
            entry['timestamp'] = timestamp.timestamp()
            # Extract message before passing entry to data to avoid duplication
            message = entry.pop('message', '')
            event = Event(
                datetime=timestamp,
                message=message,
                module=module,
                timestamp_desc=timestamp_desc,
                data=entry
            )
            return event.to_dict()
        '''
        jq '. |= keys' logarchive-native.json > native_keys.txt
        sort native_keys.txt | uniq -c | sort -n > native_keys_sort_unique.txt
        '''

        mapper = {
            # our own fields
            'timestamp_desc': 'timestamp_desc',
            'module': 'module',
            # logarchive fields
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
        # convert time
        timestamp = datetime.fromisoformat(entry['timestamp'])
        event = Event(
            datetime=timestamp,
            message=entry.get('eventMessage', ''),
            module=module,
            timestamp_desc=timestamp_desc
        )
        entry.pop('eventMessage')
        entry.pop('timestamp')

        for key, value in entry.items():
            if key in mapper:
                new_key = mapper[key]
                if 'uuid' in new_key:  # remove - in UUID
                    event.data[new_key] = value.replace('-', '')
                else:
                    event.data[new_key] = value
            else:
                # keep the non-matching entries
                event.data[key] = value
        return event.to_dict()

    def convert_native_time_to_unifiedlog_format(time: str) -> int:
        timestamp = datetime.fromisoformat(time)
        return int(timestamp.timestamp() * 1000000000)

    def convert_unifiedlog_time_to_datetime(time: int) -> datetime:
        # convert time to datetime object
        timestamp = datetime.fromtimestamp(time / 1000000000, tz=timezone.utc)
        return timestamp
