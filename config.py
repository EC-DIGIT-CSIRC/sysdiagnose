import os
import json
"""
This file contains all of the configuration values for the project.
"""

config_folder = os.path.dirname(os.path.abspath(__file__))
parsers_folder = os.path.join(config_folder, "parsers")
analysers_folder = os.path.join(config_folder, "analysers")

# case data is in current working directory by default
cases_root_folder = os.getenv('SYSDIAGNOSE_CASES_PATH')
if not cases_root_folder:
    cases_root_folder = '.'

os.makedirs(cases_root_folder, exist_ok=True)

cases_file = os.path.join(cases_root_folder, "cases.json")
data_folder = os.path.join(cases_root_folder, "data")
parsed_data_folder = os.path.join(cases_root_folder, "parsed_data")  # stay in current folder

os.makedirs(data_folder, exist_ok=True)
os.makedirs(parsed_data_folder, exist_ok=True)


# migration of old cases format to new format
try:
    with open(cases_file, 'r') as f:
        cases = json.load(f)
        if 'cases' in cases:  # conversion is needed
            new_format = {}
            for case in cases['cases']:
                case['case_id'] = str(case['case_id'])
                new_format[case['case_id']] = case

            cases = new_format
            with open(cases_file, 'w') as f:
                json.dump(cases, f, indent=4)
except FileNotFoundError:
    cases = {}
