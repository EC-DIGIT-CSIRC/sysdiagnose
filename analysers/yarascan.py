import json
import yara
import os
import glob
import threading
import queue

analyser_description = "Scan the case folder using YARA rules ('./yara' or SYSDIAGNOSE_YARA_RULES_PATH)"
analyser_format = "json"

yara_rules_path = os.getenv('SYSDIAGNOSE_YARA_RULES_PATH', './yara')

# FIXME currently only looks in parsed_data folder, not the cases folder. Requires a revamp of all analysers.

# These are the commonly used external variables that can be used in the YARA rules
externals = {
    'filename': '',
    'filepath': '',
    'extension': '',
    'filetype': '',  # just a stub to allow some rules to load
    'owner': '',     # just a stub to allow some rules to load
}
# Question: What is the impact of externals? (single threaded)
# - timing without externals at all   : 1m30 - we discard a few (useful?) rules, so faster? ...
#                                         45s multithreaded (have 2 large files and 16 threads)
# - timing without externals per file : 1m30 - loaded empty externals, just to ensure rules are equivalent
#                                         47s multithreaded (have 2 large files and 16 threads)
# - timing with externals per file    : 4m  - delays caused by the many yara.compile calls.
# - timing with externals per file MT:  1m    multithreaded (have 2 large files and 16 threads)


def analyse_path(case_folder: str, output_file: str = "yarascan.json") -> bool:
    results = {'errors': [], 'matches': []}

    if not os.path.isdir(yara_rules_path):
        raise FileNotFoundError(f"Could not find the YARA rules folder: {yara_rules_path}")

    rule_files, errors = get_valid_yara_rule_files(yara_rules_path)
    if errors:
        results['errors'] = errors
    if len(rule_files) == 0:
        results['errors'].append(f"No valid YARA rules were present in the YARA rules folder: {yara_rules_path}")
    rule_filepaths = {}  # we need to convert the list of rule files to a dictionary for yara.compile
    for rule_file in rule_files:
        namespace = rule_file[len(yara_rules_path):].strip(os.path.sep)
        rule_filepaths[namespace] = rule_file

    matches, errors = scan_directory(case_folder, rule_filepaths, ignore_files=[output_file])
    if errors:
        results['errors'].extend(errors)
    results['matches'] = matches

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
    return


def get_valid_yara_rule_files(rules_path: str) -> tuple[list, list]:
    rule_files_to_test = glob.glob(os.path.join(yara_rules_path, '**', '*.yar'), recursive=True)
    rule_files_validated = []
    errors = []
    for rule_file in rule_files_to_test:
        if not os.path.isfile(rule_file):
            continue
        print(f"Loading YARA rule: {rule_file}")
        try:
            yara.compile(filepath=rule_file, externals=externals)
            # if we reach this point, the rule is valid
            rule_files_validated.append(rule_file)
        except yara.SyntaxError as e:
            print(f"Error compiling rule {rule_file}: {str(e)}")
            errors.append(f"Error compiling rule {rule_file}: {str(e)}")
            continue
        except yara.Error as e:
            print(f"Error compiling rule {rule_file}: {str(e)}")
            errors.append(f"Error loading rule {rule_file}: {str(e)}")
            continue

    return rule_files_validated, errors


def scan_directory(directory: str, rule_filepaths: dict, ignore_files: list) -> tuple[list, list]:
    results_lock = threading.Lock()
    matches = {}
    errors = []

    # multi-threaded file scanning, really speeds up if multiple large files are present

    # build and fill the queue
    file_queue = queue.Queue()
    for root, _, files in os.walk(directory):
        for file in files:
            if file in ignore_files:  # skip the output file, as we know we may have matches on ourselves
                continue
            file_queue.put(os.path.join(root, file))

    # define our consumer that will run in the threads
    def consumer():
        while True:
            print(f"Consumer thread seeing {file_queue.qsize()} files in queue, and taking one")
            file_path = file_queue.get()
            if file_path is None:
                print("Consumer thread exiting")
                break

            print(f"Scanning file: {file_path}")
            # set the externals for this file
            externals['filename'] = file
            externals['filepath'] = file_path[len(directory) + 1:]  # exclude the case root directory that installation specific
            externals['extension'] = os.path.splitext(file)[1]
            rules = yara.compile(filepaths=rule_filepaths, externals=externals)
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

    max_threads = os.cpu_count() or 4  # default to 4 if we can't determine the number of CPUs
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
