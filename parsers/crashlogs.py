import glob
import os
from utils.base import BaseParserInterface
import re
import json
from datetime import datetime, timezone
# from pycrashreport.crash_report import get_crash_report_from_file


class CrashLogsParser(BaseParserInterface):
    '''
    # TODO Have a look at the interesting evidence first, see which files are there that are not on other devices
    - crashes_and_spins folder
    - ExcUserFault file
    - crashes_and_spins/Panics subfolder
    - summaries/crashes_and_spins.log

    Though one as there is not necessary a fixed structure
    - first line is json
    - rest depends ...

    Or perhaps include that in a normal log-parser.
    And do the secret magic in the hunting rule
    '''

    description = 'Parsing crashes folder'
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            '**/crashes_and_spins/*.ips',
            '**/summaries/crashes_and_spins.log',
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_folder, log_files_glob), recursive=True))

        return log_files

    def execute(self) -> list | dict:
        files = self.get_log_files()
        result = []
        seen = set()
        for file in files:
            print(f"Processing file: {file}")
            if file.endswith('crashes_and_spins.log'):
                result.extend(CrashLogsParser.parse_summary_file(file))
            elif os.path.basename(file).startswith('.'):
                pass
            elif file.endswith('.ips'):
                try:
                    ips = CrashLogsParser.parse_ips_file(file)
                    ips_hash = f"{ips.get('timestamp', '')}-{ips.get('app_name', '')}"
                    # skip duplicates
                    if ips_hash in seen:
                        continue
                    seen.add(ips_hash)
                    result.append(ips)
                except Exception as e:
                    print(f"Skipping file due to error {file}: {e}")
        return result

    def parse_ips_file(path: str) -> list | dict:
        # identify the type of file
        with open(path, 'r') as f:
            result = json.loads(f.readline())  # first line
            result['report'] = {}
            lines = f.readlines()

            # next section is json structure
            if lines[0].startswith('{') and lines[len(lines) - 1].strip().endswith('}'):
                result['report'] = json.loads('\n'.join(lines))

            else:
                # next section is structured text
                # either key: value
                # or key:
                #      multiple lines
                #    key:
                #      multiple lines
                n = 0
                while n < len(lines):
                    line = lines[n].strip()

                    if not line:
                        n += 1
                        continue

                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        if value.strip():
                            result['report'][key] = value.strip()
                        else:
                            result['report'][key] = []
                            n += 1
                            while n < len(lines):
                                line = lines[n].strip()
                                if not line:    # end of section
                                    break

                                if 'Thread' in key and 'crashed with ARM Thread State' in key:
                                    if result['report'][key] == []:
                                        result['report'][key] = {}
                                    result['report'][key].update(CrashLogsParser.split_thread_crashes_with_arm_thread_state(line))
                                elif 'Binary Images' in key:
                                    result['report'][key].append(CrashLogsParser.split_binary_images(line))
                                elif 'Thread' in key:
                                    result['report'][key].append(CrashLogsParser.split_thread(line))
                                else:
                                    result['report'][key].append(line)
                                n += 1
                    elif line == 'EOF':
                        break
                    else:
                        raise Exception(f"Parser bug: Unexpected line in crashlogs at line {n}. Line: {line}")

                    n += 1

            timestamp = datetime.strptime(result['timestamp'], '%Y-%m-%d %H:%M:%S.%f %z')
            result['timestamp_orig'] = result['timestamp']
            result['datetime'] = timestamp.isoformat()
            result['timestamp'] = timestamp.timestamp()
            return result

    def parse_summary_file(path: str) -> list | dict:
        print(f"Parsing summary file: {path}")
        result = []
        with open(path, 'r') as f:
            for line in f:
                if not line.startswith('/'):
                    continue

                app, timestamp = CrashLogsParser.metadata_from_filename(line)
                path = line.split(',')[0]
                entry = {
                    'app_name': app,
                    'name': app,
                    'datetime': timestamp.isoformat(),
                    'timestamp': timestamp.timestamp(),
                    'filename': os.path.basename(path),
                    'path': path,
                    'warning': 'Timezone not considered, parsed local time as UTC'
                    # FIXME timezone is from local phone time at file creation. Not UTC
                }
                result.append(entry)
        return result

    def split_thread_crashes_with_arm_thread_state(line) -> dict:
        elements = line.split()
        result = {}
        for i in range(0, len(elements), 2):
            if not elements[i].endswith(':'):
                break   # last entry is not a valid key:value
            result[elements[i][:-1]] = elements[i + 1]
        return result

    def split_thread(line) -> dict:
        elements = line.split()
        result = {
            'id': elements[0],
            'image_name': elements[1],
            'image_base': elements[2],
            'image_offset': elements[3],
            'symbol_offset': elements[5]
        }
        return result

    def split_binary_images(line) -> dict:
        elements = line.split()
        result = {
            'image_offset_start': elements[0],
            'image_offset_end': elements[2],
            'image_name': elements[3],
            'arch': elements[4],
            'uuid': elements[5][1:-1],
            'path': elements[6],
        }
        return result

    def metadata_from_filename(filename: str) -> tuple[str, datetime]:
        while True:
            # option 1: YYYY-MM-DD-HHMMSS
            m = re.search(r'/([^/]+)-(\d{4}-\d{2}-\d{2}-\d{6})', filename)
            if m:
                timestamp = datetime.strptime(m.group(2), '%Y-%m-%d-%H%M%S')
                break
            # option 2: YYYY-MM-DD-HH-MM-SS
            m = re.search(r'/([^/]+)-(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})', filename)
            if m:
                timestamp = datetime.strptime(m.group(2), '%Y-%m-%d-%H-%M-%S')
                break
            # fallback, basename
            app = os.path.basename(filename)
            return app, datetime.fromtimestamp(0, tz=timezone.utc)

        app = m.group(1)
        # FIXME timezone is from local phone time at file creation. Not UTC
        timestamp = timestamp.replace(tzinfo=timezone.utc)
        return app, timestamp
