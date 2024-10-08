#! /usr/bin/env python3

# For Python3
# Script to parse the swcutil_show.txt file
# Author: Emilien Le Jamtel

import glob
import os
import re
from sysdiagnose.utils.base import BaseParserInterface
from datetime import datetime, timedelta, timezone


class SpindumpNoSymbolsParser(BaseParserInterface):
    description = 'Parsing spindump-nosymbols file'
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'spindump-nosymbols.txt'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list:
        return SpindumpNoSymbolsParser.parse_file(self.get_log_files()[0])

    def parse_file(path: str) -> list:
        try:
            with open(path, 'r') as f_in:
                # init section
                headers = []
                processes_raw = []
                status = 'headers'

                # stripping
                for line in f_in:
                    if line.strip() == "" or line.strip() == "Heavy format: stacks are sorted by count" or line.strip() == "Use -i and -timeline to re-report with chronological sorting":
                        continue
                    elif line.strip() == "------------------------------------------------------------":
                        status = 'processes_raw'
                        continue
                    elif line.strip() == "Spindump binary format":
                        status = 'binary'
                        continue
                    elif status == 'headers':
                        headers.append(line.strip())
                        continue
                    elif status == 'processes_raw':
                        processes_raw.append(line.strip())
                        continue

                # call parsing function per section
                events = []
                basic = SpindumpNoSymbolsParser.parse_basic(headers)
                events.append(basic)
                events.extend(SpindumpNoSymbolsParser.parse_processes(processes_raw, start_timestamp=basic['timestamp']))

                return events

        except IndexError:
            return []

    def parse_basic(data: list) -> dict:
        output = {}
        for line in data:
            splitted = line.split(":", 1)
            if len(splitted) > 1:
                output[splitted[0]] = splitted[1].strip()

        if 'Date/Time' in output:
            timestamp = datetime.strptime(output['Date/Time'], "%Y-%m-%d %H:%M:%S.%f %z")
            output['timestamp'] = timestamp.timestamp()
            output['datetime'] = timestamp.isoformat(timespec='microseconds')

        return output

    def parse_processes(data: list, start_timestamp: int) -> list[dict]:
        # init
        start_time = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)
        processes = []
        init = True
        process_buffer = []
        for line in data:
            if "Process:" in line.strip():
                if not init:
                    process = SpindumpNoSymbolsParser.parse_process(process_buffer)
                    try:
                        timestamp = start_time - timedelta(seconds=int(process['Time Since Fork'].rstrip('s')))
                    except KeyError:  # some don't have a time since fork, like zombie processes
                        timestamp = start_time
                    process['timestamp'] = timestamp.timestamp()
                    process['datetime'] = timestamp.isoformat(timespec='microseconds')
                    processes.append(process)
                    process_buffer = [line.strip()]
                else:
                    init = False
                    process_buffer.append(line.strip())
            else:
                process_buffer.append(line.strip())

        process = SpindumpNoSymbolsParser.parse_process(process_buffer)
        timestamp = start_time - timedelta(seconds=int(process['Time Since Fork'].rstrip('s')))
        process['timestamp'] = timestamp.timestamp()
        process['datetime'] = timestamp.isoformat(timespec='microseconds')
        processes.append(process)
        return processes

    def parse_process(data):
        # init
        status = 'infos'
        infos = []
        threads = []
        images = []
        for line in data:
            if "Thread 0x" in line.strip():
                status = "threads"
                threads.append(line.strip())
                continue
            elif "Binary Images:" in line.strip():
                status = "images"
                continue
            elif status == "infos":
                infos.append(line.strip())
                continue
            elif status == "threads":
                threads.append(line.strip())
                continue
            elif status == "images":
                images.append(line.strip())
                continue
        process = SpindumpNoSymbolsParser.parse_basic(infos)
        process['threads'] = SpindumpNoSymbolsParser.parse_threads(threads)
        process['images'] = SpindumpNoSymbolsParser.parse_images(images)
        # parse special substrings
        process['PID'] = int(re.search(r'\[(\d+)\]', process['Process']).group(1))
        process['Process'] = process['Process'].split("[", 1)[0].strip()
        try:
            process['PPID'] = int(re.search(r'\[(\d+)\]', process['Parent']).group(1))
            process['Parent'] = process['Parent'].split("[", 1)[0].strip()
        except KeyError:  # some don't have a parent
            pass
        process['UID'] = 501
        return process

    def parse_threads(data):
        # init
        init = True
        threads = []
        thread = []
        for line in data:
            if "Thread 0x" in line.strip():
                if not init:
                    threads.append(SpindumpNoSymbolsParser.parse_thread(thread))
                    thread = [line.strip()]
                else:
                    init = False
                    thread.append(line.strip())
            else:
                thread.append(line.strip())
        threads.append(SpindumpNoSymbolsParser.parse_thread(thread))
        return threads

    def parse_thread(data):
        output = {}
        # parse first line
        # Thread Hex value
        threadHEXregex = re.search(r"Thread 0x..", data[0])
        output['thread'] = threadHEXregex.group(0).split(" ", 1)[1]
        # Thread Name / DispatchQueue
        if "DispatchQueue \"" in data[0]:
            dispacthregex = re.search(r"DispatchQueue(.*)\"\(", data[0])
            output['DispatchQueue'] = dispacthregex.group(0).split("\"")[1]
        if "Thread name \"" in data[0]:
            dispacthregex = re.search(r"Thread name\ \"(.*)\"", data[0])
            output['ThreadName'] = dispacthregex.group(0).split("\"")[1]
        # priority
        if "priority" in data[0]:
            priorityregex = re.search(r"priority\ [0-9]+", data[0])
            output['priority'] = priorityregex.group(0).split(" ", 1)[1]
        if "cpu time" in data[0]:
            cputimeregex = re.search(r"cpu\ time\ (.*)\)", data[0])
            output["cputime"] = cputimeregex.group(0).split("time ", 1)[1]

        output["loaded"] = []

        for line in data[1:]:
            loaded = {}
            if "+" in line:
                loaded["library"] = line.split("(", 1)[1].split("+", 1)[0].strip()
                loaded["int"] = line.split("(", 1)[1].split("+", 1)[1].split(")", 1)[0].strip()
                loaded["hex"] = line.split("[", 1)[1][:-1].strip()
            elif "truncated backtrace>" not in line:
                loaded["hex"] = line.split("[", 1)[1][:-1].strip()
            output["loaded"].append(loaded)
        return output

    def parse_images(data):
        images = []
        for line in data:
            image = {}
            if line.strip() is not None:
                clean = ' '.join(line.split(" ")).split()
                image['start'] = clean[0]
                image['end'] = clean[2]
                image['image'] = clean[3]
                image['UUID'] = clean[4][1:-1]
                try:
                    image['path'] = clean[5]
                except:     # noqa E722
                    pass
                images.append(image)
        return images
