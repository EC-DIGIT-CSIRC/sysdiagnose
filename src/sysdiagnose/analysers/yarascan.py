import glob
import json
import os
import queue
import threading
from datetime import datetime

import yara
from sysdiagnose.utils.base import BaseAnalyserInterface, Event, SysdiagnoseConfig, logger

# These are the commonly used external variables that can be used in the YARA rules
externals = {
    'filename': '',
    'filepath': '',
    'extension': '',
    'filetype': '',  # just a stub to allow some rules to load
    'owner': '',     # just a stub to allow some rules to load
}


class YaraAnalyser(BaseAnalyserInterface):
    description = "Scan the case folder using YARA rules ('./yara' or SYSDIAGNOSE_YARA_RULES_PATH)"
    format = "jsonl"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)
        self.yara_rules_path = os.getenv('SYSDIAGNOSE_YARA_RULES_PATH', './yara')

    # Question: What is the impact of externals? (single threaded)
    # - timing without externals at all   : 1m30 - we discard a few (useful?) rules, so faster? ...
    #                                         45s multithreaded (have 2 large files and 16 threads)
    # - timing without externals per file : 1m30 - loaded empty externals, just to ensure rules are equivalent
    #                                         47s multithreaded (have 2 large files and 16 threads)
    # - timing with externals per file    : 4m  - delays caused by the many yara.compile calls.
    # - timing with externals per file MT:  1m    multithreaded (have 2 large files and 16 threads)

    def execute(self):
        file_queue = self.get_target_files(
            directories=[
                self.case_parsed_data_folder,
                self.case_data_folder
            ],
            ignore_files=[
                self.output_file,         # don't match on ourselves
            ],
            ignore_folders=[
                glob.glob(os.path.join(self.case_data_subfolder, 'system_logs.logarchive')).pop(),  # irrelevant for YARA rules
            ]
        )

        rule_filepaths = self.get_valid_yara_rule_files()
        rules = yara.compile(filepaths=rule_filepaths, externals=externals)

        results = []
        self.threaded_scan_files(file_queue, rules, results)
        return results

    def get_valid_yara_rule_files(self) -> dict:
        """
        Scans the YARA rules directory for valid .yar files and compiles them to ensure
        they are valid YARA rules. Returns a dictionary of rule file paths indexed by their namespace

        :raises FileNotFoundError: If the YARA rules directory does not exist
        :raises yara.Error: If there is an error compiling a YARA rule

        :return: Dictionary of valid YARA rule file paths
        """
        if not os.path.isdir(self.yara_rules_path):
            raise FileNotFoundError(f"YARA rules folder not found: {self.yara_rules_path}")

        rule_filepaths = {}
        rule_files_to_test = glob.glob(os.path.join(self.yara_rules_path, '**', '*.yar'), recursive=True)
        for rule_file in rule_files_to_test:
            if not os.path.isfile(rule_file):
                continue
            logger.info(f"Loading YARA rule: {rule_file}", extra={'yara_rule_file': rule_file})
            try:
                yara.compile(filepath=rule_file, externals=externals)
                # Valid rule, add it to the rule_filepaths
                namespace = rule_file[len(self.yara_rules_path):].strip(os.path.sep)
                rule_filepaths[namespace] = rule_file
            except yara.SyntaxError:
                logger.exception(f"Error compiling rule {rule_file}", extra={'yara_rule_file': rule_file})
                continue
            except yara.Error:
                logger.exception(f"Error compiling rule {rule_file}", extra={'yara_rule_file': rule_file})
                continue

        if rule_filepaths:
            return rule_filepaths
        else:
            raise ValueError(f"No valid YARA rules (.yar) were found in the YARA rules folder: {self.yara_rules_path}")

    @staticmethod
    def get_target_files(directories: list, ignore_files: list, ignore_folders: list) -> queue.Queue:
        """
        Create a queue of files to be scanned by YARA.

        :param directories: List of directories to scan
        :param ignore_files: List of files to ignore
        :param ignore_folders: List of folders to ignore
        :return: A queue containing the file paths to be scanned
        """
        file_queue = queue.Queue()
        for directory in directories:
            for root, _, files in os.walk(directory):
                stop = False
                for ignore_folder in ignore_folders:
                    if root.startswith(ignore_folder):
                        stop = True
                        logger.warning(f"Skipping folder: {root}", extra={'yara_ignored_path': root})
                        continue
                if stop:
                    continue
                for file in files:
                    file_full_path = os.path.join(root, file)
                    stop = False
                    for ignore_file in ignore_files:
                        if file_full_path.startswith(ignore_file):
                            stop = True
                            logger.warning(f"Skipping file: {file_full_path}", extra={'yara_ignored_path': file_full_path})
                            continue
                    if stop:
                        continue
                    file_queue.put(file_full_path)
        return file_queue

    @staticmethod
    def extract_line(file_path: str, instance_offset: int, instance_length: int,
                     is_jsonl: bool, length: int = 10) -> tuple[str, str]:
        """
        Extract an excerpt from a file at a given offset. In case of JSONL files, it extracts the full line.

        :param file_path: The path to the file
        :param instance_offset: The offset in the file where the match was found
        :param instance_lenght: The length of the match
        :param is_jsonl: Whether the file is a JSONL file
        :param length: The number of bytes to read before and after the match (default is 10)
        :return: A tuple with the whole line, in case it is a jsonl, if not empty, and a substring of the match
        """
        with open(file_path, 'rb') as f:
            f.seek(instance_offset)
            # Extrac the excerpt around the match
            min_length = max(length, instance_length)
            f.seek(max(0, instance_offset - min_length))
            excerpt = f.read(min_length * 3).decode(errors='replace')

            # Attempt to read the full line if it is a JSONL file
            line = ''
            if is_jsonl:
                f.seek(instance_offset)
                # Move to the start of the line
                while f.tell() > 0:
                    f.seek(-1, 1)
                    if f.read(1) == b'\n':
                        break
                    f.seek(-1, 1)
                # Now read the line
                line = f.readline().decode(errors='replace').strip()

            return line, excerpt

    def scan_file(self, file_path: str, rules: yara.Rules) -> list:
        """
        Scan a single file with the provided YARA rules.

        :param file_path: The path to the file to be scanned
        :param rules: Compiled YARA rules
        :return: A list of events containing the matches found in the file
        """
        result = []
        try:
            matches = rules.match(file_path)

            logger.info(f"Scanned file {file_path} resulted in {len(matches)} matches",
                        extra={'yara_target_file': file_path, 'yara_matches': len(matches)})

            # Timestamp for the match
            match_datetime = self.sysdiagnose_creation_datetime
            match_datetime_desc = 'Sysdiagnose creation datetime'
            # Check if the file belongs to parsed_data
            is_parsed_data = file_path.startswith(self.case_parsed_data_folder)
            relative_path = file_path[len(self.config.get_case_root_folder(self.case_id)):].lstrip(os.path.sep)
            for match in matches:
                match_details = []
                for string_match in match.strings:
                    for instance in string_match.instances:
                        # Let's extract the line from the file
                        is_parsed_data_jsonl = is_parsed_data and relative_path.endswith('.jsonl')
                        line, excerpt = YaraAnalyser.extract_line(file_path, instance.offset, instance.matched_length,
                                                                  is_parsed_data_jsonl)

                        # If the file is a parsed_data JSONL file, we can try to extract the datetime from the JSON
                        if is_parsed_data_jsonl:
                            try:
                                e = json.loads(line)  # Validate JSON
                                match_datetime = datetime.fromisoformat(e['datetime'])
                                match_datetime_desc = \
                                    f"Extracted datetime from JSON entry in {os.path.basename(relative_path)}"

                            except json.JSONDecodeError:
                                logger.exception("Error while extracting the datetime. "
                                                 f"Invalid JSON in {file_path} at offset {instance.offset}. Setting default datetime.",
                                                 extra={'yara_target_file': file_path})

                            except KeyError:
                                logger.exception("Error while extracting the datetime.")

                        # match details
                        match_details.append(
                            f"Id: '{string_match.identifier}', "
                            f"XOR: '{string_match.is_xor()}', "
                            f"plaintext: '{instance.plaintext().decode(errors='replace')}', "
                            f"offset: '{instance.offset}', "
                            f"excerpt: '{excerpt.strip()}'")

                        # Prepare the data to be returned
                        data = {
                            'target_file': relative_path,
                            'yara_rule_file': match.namespace,
                            'yara_rule': match.rule,
                            'yara_rule_meta': match.meta,
                            'yara_rule_tags': match.tags,
                            'yara_rule_match_details': match_details
                        }
                        message = f"YARA rule {match.rule} from {match.namespace} matched in {relative_path}"
                        event = Event(
                            datetime=match_datetime,
                            message=message,
                            module=self.module_name,
                            timestamp_desc=match_datetime_desc,
                            data=data,
                        )
                        result.append(event.to_dict())
        except yara.Error as e:
            logger.exception(f"Error when scanning file {file_path}", extra={'yara_target_file': file_path})

        return result

    def threaded_scan_files(self, file_queue: queue.Queue, rules: yara.Rules, results: list):
        """
        Threaded worker function to scan files from the queue using the provided YARA rules.
        :param file_queue: Queue containing file paths to be scanned
        :param rules: Compiled YARA rules
        :param results: List to store the results of the scans
        """
        results_lock = threading.Lock()

        def worker():
            while True:
                logger.debug(f"Worker thread seeing {file_queue.qsize()} files in queue, and taking one")
                file_path = file_queue.get()
                if file_path is None:
                    file_queue.task_done()
                    logger.debug("Worker thread exiting")
                    break
                matches = self.scan_file(file_path, rules)
                if matches:
                    with results_lock:
                        results.extend(matches)
                file_queue.task_done()

        # Start threads
        num_threads = max((os.cpu_count() or 0) * 2, 4)
        logger.info(f"Starting {num_threads} worker threads for YARA scanning")
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
        # Wait for queue to empty
        file_queue.join()
        # Stop threads
        for _ in threads:
            file_queue.put(None)
        for t in threads:
            t.join()

        return results
