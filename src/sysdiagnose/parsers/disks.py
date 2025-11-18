#! /usr/bin/env python3

# For Python3
# Parser for disks.txt (df-like output) to extract per-mount capacity/usage
# Author: envoid helpers

import glob
import os
import re

from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger, Event
from sysdiagnose.utils.misc import snake_case


def _parse_size_to_bytes(size_str: str) -> int:
    """
    Convert a human-readable size string to bytes.

    Accepts suffixes: B, K, M, G, T (case-insensitive). If no suffix, try int.
    """
    if size_str is None:
        return 0
    s = str(size_str).strip()
    if s == '' or s == '-':
        return 0
    try:
        # raw bytes
        return int(s)
    except ValueError:
        pass

    match = re.fullmatch(r"(?i)([0-9]+)([bkmg t])?", s.replace(' ', ''))
    if not match:
        # could be in blocks like "324k" (inodes), still handle the suffix scale
        match = re.fullmatch(r"(?i)([0-9]+\.?[0-9]*)([bkmg t%])?", s.replace(' ', ''))
    if not match:
        return 0

    num_str = match.group(1)
    unit = (match.group(2) or '').strip().upper()
    try:
        value = float(num_str)
    except ValueError:
        return 0

    factor = 1
    if unit == 'B' or unit == '':
        factor = 1
    elif unit == 'K':
        factor = 1024
    elif unit == 'M':
        factor = 1024 ** 2
    elif unit == 'G':
        factor = 1024 ** 3
    elif unit == 'T':
        factor = 1024 ** 4
    else:
        # unknown suffix (%, etc.)
        factor = 1

    return int(value * factor)


class DisksParser(BaseParserInterface):
    description = "Parsing disks.txt file (df output)"
    format = "jsonl"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'disks.txt'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            for item in glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)):
                if os.path.getsize(item) > 0:
                    log_files.append(item)
        return log_files

    def execute(self) -> list | dict:
        files = self.get_log_files()
        if not files:
            return {'error': ['No disks.txt file present']}
        result: list = []
        for file_path in files:
            result.extend(self.parse_file(file_path))
        return result

    def parse_file(self, filename: str) -> list:
        events: list = []
        timestamp = self.sysdiagnose_creation_datetime

        try:
            with open(filename, 'r') as f:
                header_line = f.readline()
                if not header_line:
                    return events
                # Split header by runs of whitespace
                # Merge common multi-word header 'Mounted on' into a single token
                header_sane = header_line.replace('Mounted on', 'Mounted_on')
                header = re.split(r"\s+", header_sane.strip())
                header_length = len(header)

                # Normalize header names
                normalized_header = [snake_case(h) for h in header]

                for line in f:
                    line = line.rstrip('\n')
                    if not line.strip():
                        continue

                    # Split into header_length fields, last field may contain spaces (mount path)
                    fields = line.strip().split(None, header_length - 1)
                    if len(fields) < header_length:
                        # skip malformed line
                        continue

                    entry: dict = {}
                    for idx, col_name in enumerate(normalized_header):
                        value = fields[idx]
                        # Keep raw and try to provide numeric versions for size/usage columns
                        entry[col_name] = value

                    # Add derived bytes fields when possible
                    for size_key in ('size', 'used', 'avail'):
                        if size_key in entry:
                            entry[f'{size_key}_bytes'] = _parse_size_to_bytes(entry[size_key])

                    # Normalize percentage fields
                    if 'capacity' in entry and isinstance(entry['capacity'], str) and entry['capacity'].endswith('%'):
                        try:
                            entry['capacity_percent'] = float(entry['capacity'].rstrip('%'))
                        except ValueError:
                            pass
                    if 'use%' in entry:
                        try:
                            entry['use_percent'] = float(str(entry['use%']).rstrip('%'))
                        except ValueError:
                            pass

                    # Craft message and event
                    mount_point = entry.get('mounted_on') or entry.get('mount_point') or entry.get('mounted') or ''
                    filesystem = entry.get('filesystem', '')
                    msg = f"Disk usage on {mount_point} ({filesystem})"

                    event = Event(
                        datetime=timestamp,
                        message=msg,
                        module=self.module_name,
                        timestamp_desc='sysdiagnose creation time',
                        data=entry
                    )
                    events.append(event.to_dict())
        except Exception:
            logger.exception("Could not parse disks.txt")

        return events
