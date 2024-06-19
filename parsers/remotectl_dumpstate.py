#! /usr/bin/env python3
import glob
import os
from utils.tabbasedhierarchy import parse_tab_based_hierarchal_file

parser_description = "Parsing remotectl_dumpstate file containing system information"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'remotectl_dumpstate.txt'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    try:
        return parse_tab_based_hierarchal_file(get_log_files(path)[0])
    except IndexError:
        return {'error': 'No remotectl_dumpstate.txt file present'}
