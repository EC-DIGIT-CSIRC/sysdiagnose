import yara
import os
import glob
import threading
import queue
import logging
from sysdiagnose.utils.base import BaseAnalyserInterface

logger = logging.getLogger('sysdiagnose')


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
    format = "json"

    def __init__(self, config: dict, case_id: str):
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
        results = {'errors': [], 'matches': []}

        if not os.path.isdir(self.yara_rules_path):
            raise FileNotFoundError(f"Could not find the YARA rules (.yar) folder: {self.yara_rules_path}")

        rule_files, errors = self.get_valid_yara_rule_files()
        if errors:
            results['errors'] = errors
        if len(rule_files) == 0:
            results['errors'].append(f"No valid YARA rules (.yar) were present in the YARA rules folder: {self.yara_rules_path}")
        rule_filepaths = {}  # we need to convert the list of rule files to a dictionary for yara.compile
        for rule_file in rule_files:
            namespace = rule_file[len(self.yara_rules_path):].strip(os.path.sep)
            rule_filepaths[namespace] = rule_file

        if len(rule_files) > 0:
            matches, errors = YaraAnalyser.scan_directory(
                [
                    self.case_parsed_data_folder,
                    self.case_data_folder
                ],
                rule_filepaths,
                ignore_files=[
                    self.output_file,         # don't match on ourselves
                ],
                ignore_folders=[
                    glob.glob(os.path.join(self.case_data_subfolder, 'system_logs.logarchive')).pop(),  # irrelevant for YARA rules
                ]
            )
            if errors:
                results['errors'].extend(errors)
            results['matches'] = matches

        if len(results['errors']) > 0:
            logger.error("Scan finished with errors. Review the results")

        return results

    def get_valid_yara_rule_files(self) -> tuple[list, list]:
        rule_files_to_test = glob.glob(os.path.join(self.yara_rules_path, '**', '*.yar'), recursive=True)
        rule_files_validated = []
        errors = []
        for rule_file in rule_files_to_test:
            if not os.path.isfile(rule_file):
                continue
            logger.info(f"Loading YARA rule: {rule_file}")
            try:
                yara.compile(filepath=rule_file, externals=externals)
                # if we reach this point, the rule is valid
                rule_files_validated.append(rule_file)
            except yara.SyntaxError as e:
                logger.error(f"Error compiling rule {rule_file}: {str(e)}")
                errors.append(f"Error compiling rule {rule_file}: {str(e)}")
                continue
            except yara.Error as e:
                logger.error(f"Error compiling rule {rule_file}: {str(e)}")
                errors.append(f"Error loading rule {rule_file}: {str(e)}")
                continue

        return rule_files_validated, errors

    def scan_directory(directories: list, rule_filepaths: dict, ignore_files: list, ignore_folders: list) -> tuple[list, list]:
        results_lock = threading.Lock()
        matches = {}
        errors = []

        # multi-threaded file scanning, really speeds up if multiple large files are present

        # build and fill the queue
        file_queue = queue.Queue()
        for directory in directories:
            for root, _, files in os.walk(directory):
                stop = False
                for ignore_folder in ignore_folders:
                    if root.startswith(ignore_folder):
                        stop = True
                        logger.info(f"Skipping folder: {root}")
                        continue
                if stop:
                    continue
                for file in files:
                    file_full_path = os.path.join(root, file)
                    stop = False
                    for ignore_file in ignore_files:
                        if file_full_path.startswith(ignore_file):
                            stop = True
                            logger.info(f"Skipping file: {file_full_path}")
                            continue
                    if stop:
                        continue
                    file_queue.put(file_full_path)

        # define our consumer that will run in the threads
        def consumer():
            # compile rules only once ... and ignore file specific externals. Massive speedup
            rules = yara.compile(filepaths=rule_filepaths, externals=externals)

            while True:
                logger.info(f"Consumer thread seeing {file_queue.qsize()} files in queue, and taking one")
                file_path = file_queue.get()
                if file_path is None:
                    logger.info("Consumer thread exiting")
                    break

                logger.info(f"Scanning file: {file_path}")
                # set the externals for this file - massive slowdown
                # externals_local = externals.copy()
                # externals_local['filename'] = file
                # externals_local['filepath'] = file_path[len(directory) + 1:]  # exclude the case root directory that installation specific
                # externals_local['extension'] = os.path.splitext(file)[1]
                # rules = yara.compile(filepaths=rule_filepaths, externals=externals_local)
                try:
                    m = rules.match(file_path)
                    if m:
                        key = file_path[len(directory) + 1:]
                        with results_lock:
                            matches[key] = {}
                            for match in m:
                                matches[key][match.rule] = {
                                    'tags': match.tags,
                                    'meta': match.meta,
                                    'strings': [str(s) for s in match.strings],
                                    'rule_file': match.namespace
                                }
                except yara.Error as e:
                    with results_lock:
                        errors.append(f"Error matching file {file_path}: {e}")
                file_queue.task_done()  # signal that the file has been processed

        max_threads = os.cpu_count() * 2 or 4  # default to 4 if we can't determine the number of CPUs
        # Create and start consumer threads
        consumer_threads = []
        for _ in range(max_threads):
            t = threading.Thread(target=consumer)
            t.start()
            consumer_threads.append(t)

        # Wait for the queue to be empty
        file_queue.join()

        # Stop the consumer threads
        for _ in range(max_threads):
            file_queue.put(None)
        for t in consumer_threads:
            t.join()

        return matches, errors
