#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

import glob
import os

parser_description = "Parsing swcutil_show file"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'swcutil_show.txt'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    with open(get_log_files(path)[0], 'r') as f_in:
        # init section
        headers = []
        db = []
        network = []
        settings = []
        memory = []
        status = 'headers'

        # stripping
        for line in f_in:
            if line.strip() == "":
                continue
            if line.strip() == "=================================== DATABASE ===================================":
                status = 'db'
                continue
            elif line.strip() == "=================================== NETWORK ====================================":
                status = 'network'
                continue
            elif line.strip() == "=================================== SETTINGS ===================================":
                status = 'settings'
                continue
            elif line.strip() == "================================= MEMORY USAGE =================================":
                status = 'memory'
                continue
            elif status == 'headers':
                headers.append(line.strip())
                continue
            elif status == 'db':
                db.append(line.strip())
                continue
            elif status == 'network':
                network.append(line.strip())
                continue
            elif status == 'settings':
                settings.append(line.strip())
                continue
            elif status == 'memory':
                memory.append(line.strip())
                continue

        # call parsing function per section
        parsed_headers = parse_basic(headers)
        parsed_db = parse_db(db)
        parsed_network = parse_basic(network)
        parsed_settings = parse_basic(settings)
        parsed_memory = parse_basic(memory)

    return {'headers': parsed_headers, 'db': parsed_db, 'network': parsed_network, 'settings': parsed_settings, 'memory': parsed_memory}


def parse_basic(data):
    output = {}
    for line in data:
        splitted = line.split(":", 1)
        if len(splitted) > 1:
            output[splitted[0]] = splitted[1].strip()
    return output


def parse_db(data):
    # init
    db = []
    db_data = []
    for line in data:
        if line.strip() == "--------------------------------------------------------------------------------":
            db.append(parse_basic(db_data))
            db_data = []
        else:
            db_data.append(line.strip())
    return db
