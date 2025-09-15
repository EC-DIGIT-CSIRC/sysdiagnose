#! /usr/bin/env python3

from io import BufferedReader
import os
import re
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger


class IOServiceParser(BaseParserInterface):
    description = "IOService.txt file parser"
    format = "json"
    rollback_addr = None
    line = None
    open_file = None

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_file = "ioreg/IOService.txt"
        return [os.path.join(self.case_data_subfolder, log_file)]

    def execute(self) -> list | dict:
        log_files = self.get_log_files()
        data_tree = {}

        for log_file in log_files:
            try:
                logger.info(f"Processing file {log_file}, new entry added", extra={'log_file': log_file})
                self.parse_file(log_file, data_tree)

            except Exception:
                logger.exception("IOService parsing crashed")

        return data_tree

    def parse_file(self, file: str, data_tree: dict):
        """           IOService file notes

            # Regex for +-o starting at start of file -> 1213 results
            (\s|\|)*\+-o

            # Regex for ALL +-o - 1213 results
            \+-o

            So we know that the data doesn't contain the node identifier ('+-o')

        """  # noqa: W605
        with open(file, 'rb') as f:
            self.open_file = f
            self.recursive_fun(data_tree)
            self.open_file = None

    def get_line(self):
        self.rollback_addr = self.open_file.tell()
        self.line = self.safe_readline(self.open_file)
        self.line = self.line.replace('\n', '')

    def safe_readline(self, open_file: BufferedReader, replacement_char: str = '?'):
        """
        Simulates readline() in binary mode, replacing non-ASCII bytes.

        This fixes an anomaly where a non-ascii (non-utf-8-) byte is present in the IOService.txt file
        (line 10797 in the testdata)
        """
        buffer = ""

        while True:
            byte = open_file.read(1)

            if not byte:  # EOF
                return buffer

            if byte == b'\n':
                return buffer
            else:
                # Check if ASCII (0–127), else replace
                if byte[0] < 128:
                    buffer += chr(byte[0])
                else:
                    buffer += replacement_char[0]

    def recursive_call(self, data_tree: dict):
        self.open_file.seek(self.rollback_addr)
        self.recursive_fun(data_tree)

    def check_start_node(self):
        if '+-o' not in self.line:
            logger.error('This is not normal. Recursive function called on random line.')
            exit(1)

    def not_empty_node_check(self):
        if not self.rollback_addr:
            logger.error("+-o in two consecutive lines, not supposed to be possible")
            exit(1)

    def check_key_uniqueness(self, dictio: dict, key: str):
        if dictio.get(key):
            logger.warning('Key is already in dictionary, data may be lost')

    def fetch_node_data(self, data_tree: dict) -> bool:
        node_data = []  # array of lines, to be transformed in json
        res = True

        while '+-o' not in self.line:
            if not self.line:   # end of file
                res = False
                break

            node_data.append(self.line)
            self.get_line()

        data_tree['Data'] = self.node_data_to_json(node_data)
        return res

    def handle_anomalies(self, dictio: dict, data: str, key: str) -> bool:
        """
            some values overflow on the few next lines
            this condition assumes there is no '=' in the exceeding data
            (which was the case up to what I saw)

            p.s. :  if you wonder why cond4 is necessary, it is only for
                    the last leaf, which has no '|' symbols. without cond4,
                    these lines would be seen as anomalies
        """
        cond1 = not re.search(r'^\s*\|+', data)
        cond2 = len(data.strip()) > 0
        cond3 = data.strip() not in ('{', '}')
        cond4 = '=' not in data

        if cond1 and cond2 and cond3 and cond4:
            dictio[key] += data.strip()
            return True
        return False

    def node_data_to_json(self, data_array: list[str]) -> dict:
        res = {}
        key = None

        for data in data_array:
            self.handle_anomalies(res, data, key)

            # remove spaces and pipes at start
            clean_line = re.sub(r'^(\s|\|)*', '', data)

            if '=' not in clean_line:
                continue

            # split at the first equal only
            key, value = clean_line.split('=', 1)

            # remove first and last " (in case the key has more quotes inside)
            key = key.replace('"', '', 1)
            key = key[::-1].replace('"', '', 1)[::-1]
            key = key.strip()

            self.check_key_uniqueness(res, key)
            res[key] = value.strip()

        return res

    def iterate_children(self, depth: int, data_tree_list: list[dict]):
        while self.line and (self.line[depth] == '|' or self.line[depth: depth + 3] == '+-o'):
            if self.line[depth: depth + 3] == '+-o':
                data_tree_list.append({})
                self.recursive_call(data_tree_list[-1])

            else:
                self.get_line()

    def recursive_fun(self, data_tree: dict):
        is_leaf = False
        self.get_line()

        # check if we're at the start of a node
        self.check_start_node()

        node_name = self.line.split("+-o")[1].strip()
        data_tree['Name'] = node_name
        data_tree['Children'] = []
        depth = self.line.index('o')  # to identify the other nodes that have the same parent
        self.get_line()

        # check if its a leaf
        if self.line[depth] != '|':
            is_leaf = True

        # Fetch the data of the node
        if not self.fetch_node_data(data_tree):
            return  # EOF

        # stop if we're a leaf
        if is_leaf:
            self.open_file.seek(self.rollback_addr)
            return

        # sanity check
        self.not_empty_node_check()

        # Iterates over each child to call the current function
        self.iterate_children(depth, data_tree['Children'])
