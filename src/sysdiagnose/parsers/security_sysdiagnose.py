import glob
import os
import re
from sysdiagnose.utils.base import BaseParserInterface, logger
from datetime import datetime


class SecuritySysdiagnoseParser(BaseParserInterface):
    description = "Parsing security-sysdiagnose.txt file containing keychain information"
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            "security-sysdiagnose.txt"
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            for item in glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)):
                if os.path.getsize(item) > 0:
                    log_files.append(item)
        return log_files

    def execute(self) -> dict:
        log_files = self.get_log_files()
        if not log_files:
            return {'errors': ['No security-sysdiagnose.txt file present']}

        json_result = {'errors': [], 'events': [], 'meta': {}}
        with open(log_files[0], "r") as f:
            buffer = []
            buffer_section = None

            # TODO cleanup way of passing results, as this was just a small refactor from an old way of working
            for line in f:
                line = line.rstrip()
                if line == '':
                    continue
                elif line.startswith('ccstatus:'):
                    SecuritySysdiagnoseParser.process_buffer(buffer, buffer_section, json_result)
                    buffer_section = 'circle'
                    buffer = [line]
                elif line.startswith('Engine state:'):
                    SecuritySysdiagnoseParser.process_buffer(buffer, buffer_section, json_result)
                    buffer_section = 'engine_state'
                    buffer = []
                elif line.endswith('keychain state:'):
                    SecuritySysdiagnoseParser.process_buffer(buffer, buffer_section, json_result)
                    buffer_section = 'keychain_state'
                    buffer = [line]
                elif line.startswith('Analystics sysdiagnose'):
                    SecuritySysdiagnoseParser.process_buffer(buffer, buffer_section, json_result)
                    buffer_section = 'analytics'
                    buffer = []
                elif line.startswith('Client:'):
                    SecuritySysdiagnoseParser.process_buffer(buffer, buffer_section, json_result)
                    buffer_section = 'client'
                    buffer = [line]  # this line contains the client type. (trust, cloudservices, networking, ...)
                elif line.startswith('All keys and values'):
                    SecuritySysdiagnoseParser.process_buffer(buffer, buffer_section, json_result)
                    buffer_section = 'keys_and_values'
                    buffer = ['keysandvalues']
                elif line.startswith('All values in'):
                    SecuritySysdiagnoseParser.process_buffer(buffer, buffer_section, json_result)
                    buffer_section = 'keys_and_values'
                    buffer = ['values']
                else:
                    buffer.append(line)

            # call the last buffer
            SecuritySysdiagnoseParser.process_buffer(buffer, buffer_section, json_result)

            # transform the 'meta' into one jsonl entry
            timestamp = self.sysdiagnose_creation_datetime
            item = {
                'timestamp': timestamp.timestamp(),
                'datetime': timestamp.isoformat(timespec='microseconds'),
                'timestamp_desc': 'sysdiagnose_creation_datetime',
                'section': 'metadata'
            }
            item.update(json_result['meta'])
            json_result['events'].append(item)

        return json_result['events']

    def process_buffer(buffer: list, section: str, json_result: dict):
        """
        process the buffer for the given section
        """
        if section is None:
            return
        function_name = f'process_buffer_{section}'
        if function_name in dir(SecuritySysdiagnoseParser):
            getattr(SecuritySysdiagnoseParser, function_name)(buffer, json_result)
        else:
            logger.error(f"ERROR: Function {function_name} not found in the SecuritySysdiagnoseParser class.")
            json_result['errors'].append(f"Cannot parse section {function_name} as it is unknown. Parser needs to be extended.")

    def process_buffer_circle(buffer: list, json_result: dict):
        """
        process the buffer for the circle section

        This section is really though to process, as there are many variants.
        As it contains interesting information about the circle of trust within the apple account
        we keep it and just add the lines as list to the result.
        TODO consider to parse the circle section in more detail
        """
        json_result['meta']['circle'] = buffer

    def process_buffer_engine_state(buffer: list, json_result: dict):
        """
        process the buffer for the engine section
        """
        line_format_local = r'^(\w+) \{([^\}]+)\} \[([0-9]+)\] (\w+)'  # noqa F841
        # LATER consider splitting up the line format
        json_result['meta']['engine'] = buffer
        pass

    def process_buffer_keychain_state(buffer: list, json_result: dict):
        """
        process the buffer for the homekit section
        """
        section = buffer.pop(0).split(' ').pop(0).lower()
        json_result['meta'][section] = []
        for line in buffer:
            # parse the csv line with key=value structure
            # unfortunately value can be { foo,bar }, so splitting on comma is not an option.
            # We need to implement a more complex parser here.
            start = line.find(': ')
            line = line[start + 2:]

            row = {}
            subsection = False
            key = None
            i = 0
            start = 0
            while i < len(line):
                if line[i] == '}':
                    subsection = False
                elif line[i] == '{':
                    subsection = True
                elif key is None and line[i] == '=':
                    key = line[start:i]
                    start = i + 1
                elif not subsection and line[i] == ',':
                    # new key value pair will start
                    # process old key value pair
                    row[key] = line[start:i]
                    start = i + 1
                    # start new key value pair
                    key = None

                i += 1
            # process the last key value pair
            row[key] = line[start:]
            json_result['meta'][section].append(row)

    def process_buffer_analytics(buffer: list, json_result: dict):
        """
        process the buffer for the analytics section
        """
        # nothing to do here
        pass

    def process_buffer_client(buffer: list, json_result: dict):
        """
        process the buffer for the client section
        """
        section = f"client_{buffer.pop(0).split(':').pop(1).lower().strip()}"
        if buffer[0].startswith('No data'):
            return

        i = 0
        while i < len(buffer):
            line = buffer[i]
            match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}) ([^:]+): (.+?) - Attributes: {(.*)', line)
            if match:
                timestamp = datetime.fromisoformat(match.group(1))
            else:
                match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2} [AP]M [+-]\d{4}) ([^:]+): (.+?) - Attributes: {(.*)', line)
                if match:
                    timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %I:%M:%S %p %z")
                else:
                    raise ValueError(f"Cannot parse line: {line}")
            row = {
                'timestamp': timestamp.timestamp(),
                'datetime': timestamp.isoformat(timespec='microseconds'),
                'section': section,
                'result': match.group(2),
                'event': match.group(3),
                'attributes': {}
            }
            attribute_string = match.group(4)

            # while next rows do not start with a date, they are part of the attributes
            try:
                while not re.search(r'^\d{4}-\d{2}-\d{2} ', buffer[i + 1]):
                    i += 1
                    attribute_string += buffer[i]
            except IndexError:
                pass
            # drop last } and split the attributes
            attribute_string = attribute_string.replace('\n', '').strip()[:-1].strip()
            attribute_pairs = re.findall(r'(\w+)\s*:\s*(\([^)]+\)|.+?)(?:, |$)', attribute_string)
            for key, value in attribute_pairs:
                row['attributes'][key.strip()] = value.strip()

            json_result['events'].append(row)
            i += 1

    def process_buffer_keys_and_values(buffer: list, json_result: dict):
        """
        process the buffer for the values section
        """
        section = buffer.pop(0)
        json_result['meta'][section] = {}

        i = 0
        while i < len(buffer):
            line = buffer[i]
            try:
                while buffer[i + 1].startswith('\t'):
                    i += 1
                    line += '\n' + buffer[i]
            except IndexError:
                pass
            key, value = line.split(': ', 1)
            json_result['meta'][section][key.strip()] = value.strip()
            i += 1
