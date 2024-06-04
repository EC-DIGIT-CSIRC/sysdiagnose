#! /usr/bin/env python3

# For Python3
# Script to print connection info from logs/appinstallation/AppUpdates.sqlite.db (iOS12)
# New version of iOS store data into logs/appinstallation/appstored.sqlitedb
# Author: david@autopsit.org

# PID: encoded in Litlle Endian??
# TODO - add support of iOS13...


from utils import sqlite2json
import glob
import os
import misc


parser_description = "Parsing app installation logs"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'logs/appinstallation/AppUpdates.sqlitedb',
        'logs/appinstallation/appstored.sqlitedb'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    return misc.json_serializable(sqlite2json.sqlite2struct(get_log_files(path)[0]))
