#! /usr/bin/env python3

import glob
import misc
import os

parser_description = "Parsing any pslist into json"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        '**/*.plist'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    return misc.load_plist_file_as_json(path)
