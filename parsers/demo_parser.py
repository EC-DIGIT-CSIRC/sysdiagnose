#! /usr/bin/env python3

import os
import json

version_string = "sysdiagnose-demo-parser.py v2023-04-26 Version 1.0"

# ----- definition for parsing.py script -----#

parser_description = "Demo parsers"

# --------------------------------------------#

# --------------------------------------------------------------------------- #


def get_log_files(log_root_path: str) -> list:
    """
        Get the list of log files to be parsed
    """
    log_files = [
        "demo_input_file.txt"
    ]
    return [os.path.join(log_root_path, log_files) for log_files in log_files]


def parse_path(path: str) -> list | dict:
    '''
        this is the function that will be called
    '''
    json_object = {}
    log_files = get_log_files(path)
    for log_file in log_files:
        pass
    return json_object


def parse_path_to_folder(path: str, output_folder: str) -> bool:
    '''
        this is the function that will be called
    '''
    try:
        json_object = {}
        log_files = get_log_files(path)
        for log_file in log_files:
            pass
        # ideally stream to the file directly
        output_folder = os.path.join(output_folder, __name__.split('.')[-1])
        os.makedirs(output_folder, exist_ok=True)
        with open(os.path.join(output_folder, "demo_output.json"), "w") as f:
            json.dump(json_object, f)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
