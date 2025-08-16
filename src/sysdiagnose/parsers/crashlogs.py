import glob
import os
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger, Event
import re
import json
from datetime import datetime, timezone
from sysdiagnose.utils.misc import load_plist_string_as_json
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

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            '**/crashes_and_spins/**/*.ips',
            '**/summaries/crashes_and_spins.log',
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_folder, log_files_glob), recursive=True))

        # exclude some files
        exclusion_strings = ['WiFiLQMMetrics', 'OTAUpdate']
        for exclusion_string in exclusion_strings:
            log_files = [x for x in log_files if exclusion_string not in x]

        return log_files

    def execute(self) -> list | dict:
        files = self.get_log_files()
        result = []
        seen = set()
        for file in files:
            logger.info(f"Processing file: {file}")
            if file.endswith('crashes_and_spins.log'):
                result.extend(self.parse_summary_file(file))
            elif os.path.basename(file).startswith('.'):
                pass
            elif file.endswith('.ips'):
                try:
                    ips = CrashLogsParser.parse_ips_file(file)
                    ips['module'] = self.module_name
                    ips_hash = f"{ips.get('timestamp', '')}-{ips.get('name', '')}"
                    # skip duplicates
                    if ips_hash in seen:
                        continue
                    seen.add(ips_hash)
                    result.append(ips)
                except Exception:
                    logger.warning(f"Skipping file due to error {file}", exc_info=True)
        return result

    def parse_ips_file(path: str) -> dict:
        # identify the type of file
        with open(path, 'r') as f:
            result = json.loads(f.readline())  # first line
            lines = f.readlines()

            result['report'] = CrashLogsParser.process_ips_lines(lines)
            timestamp = None
            if 'captureTime' in result['report']:  # captureTime is more precise than the timestamp
                timestamp = datetime.strptime(result['report']['captureTime'], '%Y-%m-%d %H:%M:%S.%f %z')
            elif 'date' in result['report']:
                try:
                    timestamp = datetime.strptime(result['report']['date'], '%Y-%m-%d %H:%M:%S.%f %z')
                except ValueError:
                    try:
                        timestamp = datetime.strptime(result['report']['date'], '%Y-%m-%d %H:%M:%SZ')
                    except ValueError:
                        timestamp = datetime.strptime(result['report']['date'], '%Y-%m-%dT%H:%M:%SZ')

            if not timestamp:
                timestamp = datetime.strptime(result['timestamp'], '%Y-%m-%d %H:%M:%S.%f %z')

            result['name'] = CrashLogsParser.metadata_from_filename(path)[0]
            try:
                message = f"Crashlog: {result['report']['reason']}"
            except KeyError:
                try:
                    message = f"Crashlog: {result['report']['procName']}"
                except KeyError:
                    message = f"Crashlog: {result['name']}"

            event = Event(
                datetime=timestamp,
                message=message,
                module='crashlogs',
                timestamp_desc='crashlog',
                data=result
            )

            return event.to_dict()

    def process_ips_lines(lines: list) -> dict:
        '''
        There are multiple main models of crashlogs:
        - one big entry nicely structured in json.
        - one big entry nicely structured as plist
        - pseudo-structured text. with multiple powerstats entries
        '''
        result = {}
        # next section is json structure
        if lines[0].startswith('{') and lines[len(lines) - 1].strip().endswith('}'):
            result = json.loads('\n'.join(lines))
            return result

        # next section is plist structure
        if lines[0].startswith('<?xml') and lines[len(lines) - 1].strip().endswith('</plist>'):
            result = load_plist_string_as_json('\n'.join(lines))
            return result

        # next section is structured text
        # either key: value
        # or key:
        #      multiple lines
        #    key:
        #      multiple lines
        # two empty lines = end of section and prepare for next powerstats entry
        # LATER this is not the cleanest way to parse this. But it works for now
        n = 0
        powerstats_key = None
        while n < len(lines):
            line = lines[n].strip()

            if not line:
                n += 1
                continue

            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()

                if 'Powerstats' in key:
                    powerstats_key = value.split()[0]
                    if 'Powerstats' not in result:
                        result['Powerstats'] = {}
                    if powerstats_key not in result['Powerstats']:
                        result['Powerstats'][powerstats_key] = {}

                # key, value entry
                if value.strip():
                    if powerstats_key:
                        result['Powerstats'][powerstats_key][key] = value.strip()
                    else:
                        result[key] = value.strip()
                # only a key, so the next lines are values
                else:
                    if powerstats_key:
                        result['Powerstats'][powerstats_key][key] = []
                    else:
                        result[key] = []
                    n += 1
                    while n < len(lines):
                        line = lines[n].strip()
                        if not line:    # end of section
                            break

                        if 'Thread' in key and 'crashed with ARM Thread State' in key:
                            if powerstats_key and result['Powerstats'][powerstats_key][key] == []:
                                result['Powerstats'][powerstats_key][key] = {}
                            else:
                                result[key] = {}

                            if powerstats_key:
                                result['Powerstats'][powerstats_key][key].update(CrashLogsParser.split_thread_crashes_with_arm_thread_state(line))
                            else:
                                result[key].update(CrashLogsParser.split_thread_crashes_with_arm_thread_state(line))

                        elif 'Binary Images' in key:
                            if powerstats_key:
                                result['Powerstats'][powerstats_key][key].append(CrashLogsParser.split_binary_images(line))
                            else:
                                result[key].append(CrashLogsParser.split_binary_images(line))

                        elif 'Thread' in key:
                            if powerstats_key:
                                result['Powerstats'][powerstats_key][key].append(CrashLogsParser.split_thread(line))
                            else:
                                result[key].append(CrashLogsParser.split_thread(line))
                        else:
                            if powerstats_key:
                                result['Powerstats'][powerstats_key][key].append(line)
                            else:
                                result[key].append(line)
                        n += 1
            elif powerstats_key:
                if 'extra_data' not in result['Powerstats'][powerstats_key]:
                    result['Powerstats'][powerstats_key]['extra_data'] = []
                result['Powerstats'][powerstats_key]['extra_data'].append(lines[n].rstrip())  # not with strip()

            elif line == 'EOF':
                break
            # elif re.match(r'[0-9]+\s+\?\?\?\s+\(', line):
            #         current_entry['unknown'] = line

            else:
                raise Exception(f"Parser bug: Unexpected line in crashlogs at line {n}. Line: {line}")

            n += 1

        return result

    def parse_summary_file(self, path: str) -> list[dict]:
        logger.info(f"Parsing summary file: {path}")
        result = []
        seen = set()  # to ensure unique entries
        with open(path, 'r') as f:
            for line in f:
                if not line.startswith('/'):
                    continue

                app, timestamp = CrashLogsParser.metadata_from_filename(line, self.sysdiagnose_creation_datetime.tzinfo)
                path = line.split(',')[0]
                event = Event(
                    datetime=timestamp,
                    message=f"Crashlog: {app}",
                    module=self.module_name,
                    timestamp_desc='crashlog',
                    data={
                        'app_name': app,
                        'name': app,
                        'filename': os.path.basename(path),
                        'path': path,
                        'warning': 'Timezone may be wrong, parsed local time as same timezone as sysdiagnose creation time'
                    }
                )

                if event.data['path'] in seen:
                    continue
                seen.add(event.data['path'])
                result.append(event.to_dict())

        return result

    def split_thread_crashes_with_arm_thread_state(line) -> dict:
        elements = line.split()
        result = {}
        for i in range(0, len(elements), 2):
            if not elements[i].endswith(':'):
                result['error'] = ' '.join(elements[i:len(elements)])
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
        # need to be regexp based
        # option 1: image_offset_start image_offset_end image_name uuid path
        m = re.search(r'\s*(\w+) -\s+([^\s]+)\s+([^<]+)<([^>]+)>\s*(.*)', line)
        elements = m.groups()
        result = {
            'image_offset_start': elements[0].strip(),
            'image_offset_end': elements[1].strip(),
            'image_name': elements[2].strip(),
            'uuid': elements[3].strip(),
            'path': elements[4].strip(),
        }
        return result

    def metadata_from_filename(filename: str, tzinfo=None) -> tuple[str, datetime]:
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
        # FIXME timezone is from local phone time at file creation. Not the TZ while creating the sysdiagnose image
        if tzinfo:
            timestamp = timestamp.replace(tzinfo=tzinfo)
        return app, timestamp
