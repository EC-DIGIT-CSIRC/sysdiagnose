#! /usr/bin/env python3

import glob
import gzip
import json
import os
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime

from sysdiagnose.utils.base import BaseParserInterface, Event, SysdiagnoseConfig, logger
from sysdiagnose.utils.misc import load_plist_bytes_as_json
from sysdiagnose.utils.summary import (
    ResultSummaryExecutionHandler,
)


def _process_section_worker(args):
    """Top-level picklable function for ProcessPoolExecutor."""
    section, creation_datetime_iso = args
    try:
        entry = load_plist_bytes_as_json(section)

        if "breakdown" in entry:
            entry["breakdown"] = "<removed by SAF>"

        if "d" in entry and "NSString" in entry["d"]:
            entry.update(LsawCsstoredumpParser.parse_plist_NSString(entry["d"]["NSString"].splitlines()))
            entry.pop("d")

        creation_datetime = datetime.fromisoformat(creation_datetime_iso)
        timestamp = creation_datetime
        timestamp_desc = "sysdiagnose creation datetime"
        if "reg date" in entry:
            timestamp_string = int(entry["reg date"][24:34])
            timestamp = datetime.fromtimestamp(timestamp_string, tz=UTC)
            timestamp_desc = "lsaw reg date"

        if "bundle id" in entry:
            message = f"lsaw: {entry['bundle id']} # {entry.get('identifier', '')}"
        elif "plugin id" in entry:
            message = f"lsaw: {entry['plugin id']} # {entry.get('identifier', '')}"
        else:
            message = f"lsaw: {entry.get('name', 'record')}"

        event = Event(
            datetime=timestamp, message=message, module="lsaw_csstoredump", timestamp_desc=timestamp_desc, data=entry
        )
        return json.dumps(event.to_dict(), ensure_ascii=False)
    except Exception:
        return None


class LsawCsstoredumpParser(BaseParserInterface):
    description = "Parse lsaw.csstoredump file"
    format = "jsonl"
    module_name = "lsaw_csstoredump"

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def get_log_files(self) -> list:
        log_files_globs = ["lsaw.csstoredump"]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        """
        this is the function that will be called
        """
        result = []
        [result.append(entry) for entry in self.parse_all_and_yield()]
        return result

    def get_result(self, force: bool = False):
        if force:
            self.save_result(force)

        if not self.output_exists():
            self.save_result()

        self.get_result_summary()
        with open(self.output_file) as f:
            for line in f:
                try:
                    yield json.loads(line)
                except json.decoder.JSONDecodeError:
                    continue

    def save_result(self, force: bool = False, indent=None):
        """
        Save the result of the parsing operation to a file in the parser output folder
        """
        if force or not self.output_exists():
            self._execute_with_result_summary(indent)
            self.save_result_summary()

    def _execute_with_result_summary(self, indent=None):
        handler = ResultSummaryExecutionHandler()
        handler.start()
        try:
            num_events = 0
            creation_dt_iso = self.sysdiagnose_creation_datetime.isoformat()
            log_files = self.get_log_files()
            with ProcessPoolExecutor() as executor, open(self.output_file, "w") as f:
                for log_file in log_files:
                    decompressed = LsawCsstoredumpParser.decompress_file(log_file)
                    sections = list(LsawCsstoredumpParser.parse_sections(decompressed))
                    args = [(s, creation_dt_iso) for s in sections]
                    for json_line in executor.map(_process_section_worker, args):
                        if json_line:
                            f.write(json_line)
                            f.write("\n")
                            num_events += 1
        except Exception:
            logger.exception("lsaw_csstoredump parsing crashed")
            handler.update(num_events=0, add_errors=1, end=True)
            self._result_summary = handler.get()
            self._result = None
            return

        handler.update(num_events=num_events, end=True)
        self._result_summary = handler.get()
        # we don't keep the result in memory, as it can be very large, so we set it to None to avoid confusion
        self._result = None

    def parse_all_and_yield(self):
        for log_file in self.get_log_files():
            lsaw_cstoredump = LsawCsstoredumpParser.decompress_file(log_file)
            sections = LsawCsstoredumpParser.parse_sections(lsaw_cstoredump)

            for section in sections:
                yield self.process_section(section)

    def process_section(self, section):
        try:
            # print(f"Processing lsaw.csstoredump section: {len(section)} bytes")
            entry = load_plist_bytes_as_json(section)

            if "breakdown" in entry:
                entry["breakdown"] = "<removed by SAF>"
            #     breakdown1_compressed = base64.b64decode(entry['breakdown'])
            #     breakdown = lzfse.decompress(breakdown1_compressed[4:])

            if "d" in entry and "NSString" in entry["d"]:
                entry.update(LsawCsstoredumpParser.parse_plist_NSString(entry["d"]["NSString"].splitlines()))
                entry.pop("d")
            else:
                pass

            # Let's get the timestamp from the event
            timestamp = self.sysdiagnose_creation_datetime
            timestamp_desc = "sysdiagnose creation datetime"
            if "reg date" in entry:
                timestamp_string = int(entry["reg date"][24:34])  # POSIX timestamp, in UTC
                timestamp = datetime.fromtimestamp(timestamp_string, tz=UTC)
                timestamp_desc = "lsaw reg date"
            # Let's build the message
            if "bundle id" in entry:
                message = f"lsaw: {entry['bundle id']} # {entry.get('identifier', '')}"  # name
            elif "plugin id" in entry:
                message = f"lsaw: {entry['plugin id']} # {entry.get('identifier', '')}"  # name
            else:
                message = f"lsaw: {entry.get('name', 'record')}"

            event = Event(
                datetime=timestamp, message=message, module=self.module_name, timestamp_desc=timestamp_desc, data=entry
            )

            return event.to_dict()
        except Exception:
            logger.exception("Error parsing lsaw.csstoredump", extra={"section": section})

    @staticmethod
    def parse_plist_NSString(lines: list) -> dict:  # noqa: N802
        entry = {}
        i = 0
        data_dict_section = False
        data_dict = {}
        while i < len(lines):
            # Record data entries
            if lines[i].startswith("+++++++++++++++++++++"):
                if "record_data" not in entry:
                    entry["record_data"] = []
                i += 1
                while i < len(lines):
                    entry["record_data"].append(lines[i])
                    i += 1
                break
            # Record data dicts
            if lines[i].startswith("----------------------------"):
                if "record_data" not in entry:
                    entry["record_data"] = []
                if data_dict:  # add previous data_dict
                    entry["record_data"].append(data_dict)
                data_dict_section = True
                data_dict = {}
                i += 1
                continue

            key = lines[i][0:28].strip(" ")
            if not key.endswith(":"):
                # logger.warning(f"Potential bug: Key does not end with colon: {lines[i]}")
                if "record_data" not in entry:
                    entry["record_data"] = []
                entry["record_data"].append(lines[i])
                i += 1
                continue
            key = key.strip(":")
            val = lines[i][28:].strip()

            if data_dict_section:
                data_dict[key] = val
            else:
                entry[key] = val

            # if next line has no key, but a value, that means it is a continuation of the previous value.
            while i + 1 < len(lines):
                next_key = lines[i + 1][0:28].strip(" :")
                next_val = lines[i + 1][28:].strip()
                if next_key == "" and next_val != "":
                    if data_dict_section:
                        data_dict[key] += " " + next_val
                    else:
                        entry[key] += " " + next_val
                    i += 1
                else:  # end of sub-entry
                    break
            i += 1

        # add last data_dict
        if data_dict_section and data_dict:
            entry["record_data"].append(data_dict)

        return entry

    @staticmethod
    def decompress_file(file_path: str) -> bytes:
        with open(file_path, "rb") as f, gzip.GzipFile(fileobj=f) as gz:
            lsaw_cstoredump = gz.read()
            return lsaw_cstoredump

    @staticmethod
    def parse_sections(data: bytes):
        """
        the first 0x10 bytes are the global header
        then 0x8 bytes are the size of the following data block
        then the new 0x8 bytes header with the length of the next data
        and so on
        """
        start_offset = 0x10
        size_length = 0x8
        offset = start_offset

        while offset < len(data):
            size = int.from_bytes(data[offset : offset + size_length], byteorder="little")
            offset += size_length
            if offset + size > len(data):
                break
            section_data = data[offset : offset + size]
            yield section_data
            offset += size


if __name__ == "__main__":
    import re
    import unicodedata

    def slugify(value, allow_unicode=False):
        """
        Taken from https://github.com/django/django/blob/master/django/utils/text.py
        Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
        dashes to single dashes. Remove characters that aren't alphanumerics,
        underscores, or hyphens. Also strip leading and
        trailing whitespace, dashes, and underscores.
        """
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize("NFKC", value)
        else:
            value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        value = re.sub(r"[^\w\s-]", "", value)
        return value

    import argparse

    from sysdiagnose import Sysdiagnose

    parser = argparse.ArgumentParser(description="Extract files from lsaw.csstoredump file.")
    parser.add_argument(
        "-c", "--case_id", required=False, default="all", help='ID of the case, or "all" for all cases (default)'
    )
    args = parser.parse_args()

    sd = Sysdiagnose()

    case_ids = sd.get_case_ids() if args.case_id == "all" else [args.case_id]

    for case_id in case_ids:
        print(f"Processing case {case_id}")  # noqa: T201
        parser = LsawCsstoredumpParser(sd.config, case_id)
        output_folder = os.path.join(parser.case_parsed_data_folder, "lsaw_csstoredump")
        os.makedirs(output_folder, exist_ok=True)
        for i, entry in enumerate(parser.parse_all_and_yield()):
            # print(entry)
            entry_name = slugify(entry["data"].get("s"))
            print(f"- entry {i} - {entry_name}")  # noqa: T201
            dest = os.path.join(output_folder, f"entry_{i:05}_{entry_name}.json")
            with open(dest, "w") as f:
                f.write(json.dumps(entry["data"], indent=2))
