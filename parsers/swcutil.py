#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

import glob
import os
from utils.base import BaseParserInterface


class SwcutilParser(BaseParserInterface):
    description = "Parsing swcutil_show file"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'swcutil_show.txt'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        return SwcutilParser.parse_file(self.get_log_files()[0])

    def parse_file(path: str) -> list | dict:
        try:
            with open(path, 'r') as f_in:
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
                parsed_headers = SwcutilParser.parse_basic(headers)
                parsed_db = SwcutilParser.parse_db(db)
                parsed_network = SwcutilParser.parse_basic(network)
                parsed_settings = SwcutilParser.parse_basic(settings)
                parsed_memory = SwcutilParser.parse_basic(memory)

            return {'headers': parsed_headers, 'db': parsed_db, 'network': parsed_network, 'settings': parsed_settings, 'memory': parsed_memory}
        except IndexError:
            return {'error': 'No swcutil_show.txt file present'}

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
                db.append(SwcutilParser.parse_basic(db_data))
                db_data = []
            else:
                db_data.append(line.strip())
        return db
