import json
import yara
import os
import glob
# import hashlib

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
# - timing without externals per file : 1m30 - loaded empty externals, just to ensure rules are equivalent
# - timing with externals per file    : 4 minutes  - delays caused by the many yara.compile calls.
# FIXME Is it worth it? 1m30 vs 4m00
externals = {}


def analyse_path(case_folder: str, output_file: str = "yara.json") -> bool:
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

    matches, errors = scan_directory(case_folder, rule_filepaths)
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


def scan_directory(directory: str, rule_filepaths: dict) -> tuple[list, list]:
    matches = {}
    errors = []

    rules = yara.compile(filepaths=rule_filepaths, externals=externals)

    # TODO consider multithreading this to speed up the process
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)

            print(f"Scanning file: {file_path}")
            # set the externals for this file
            externals['filename'] = file
            externals['filepath'] = file_path[len(directory):]  # exclude the case root directory that installation specific
            externals['extension'] = os.path.splitext(file)[1]

            # rules = yara.compile(filepaths=rule_filepaths, externals=externals)
            try:
                m = rules.match(file_path)
                if m:
                    key = file_path[len(directory):]
                    matches[key] = {}
                    for match in m:
                        matches[key][match.rule] = {
                            'tags': match.tags,
                            'meta': match.meta,
                            'strings': [str(s) for s in match.strings],
                            'rule_file': match.namespace
                        }
            except yara.Error as e:
                errors.append(f"Error matching file {file_path}: {e}")
    return matches, errors


if __name__ == "__main__":
    fname = './cases/parsed_data/4/'
    analyse_path(fname)
