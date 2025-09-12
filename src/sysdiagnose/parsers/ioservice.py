#! /usr/bin/env python3

import os
import string
from tokenize import String
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger, Event
from datetime import datetime


class DemoParser(BaseParserInterface):
    description = "Demo parsers"
    format = "json"  # by default json, use jsonl for event-based data
    rollback_addr = None
    line = None
    open_file = None

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_file = "ioreg/IOServiceTestData.txt"
        return [os.path.join(self.case_data_subfolder, log_file)]

    def execute(self) -> list | dict:
        '''
        this is the function that will be called
        '''
        result = []
        log_files = self.get_log_files()
        for log_file in log_files:
            entry = {}
            try:
                timestamp = datetime.strptime('1980-01-01 12:34:56.001 +00:00', '%Y-%m-%d %H:%M:%S.%f %z')  # moment of interest
                event = Event(
                    datetime=timestamp,
                    message=f"Demo event from {log_file}",  # String with an informative message of the event
                    module=self.module_name,
                    timestamp_desc='Demo timestamp',        # String explaining what type of timestamp it is for example file created
                )

                self.parse_file(log_file)

                result.append(event.to_dict())
                logger.info(f"Processing file {log_file}, new entry added", extra={'log_file': log_file})
                logger.debug(f"Entry details {str(entry)}", extra={'entry': str(entry)})
                if not entry:
                    logger.warning("Empty entry.")
                    
            except Exception:
                logger.exception("Got an exception !")
                
        return result
    
    def parse_file(self, file: string):
        """           IOService file notes

            # Regex for +-o starting at start of file -> 1213 results
            (\s|\|)*\+-o

            # Regex for ALL +-o - 1213 results
            \+-o

            So we know that the data doesn't contain the node identifier ('+-o')

        """
        print('===============================')
        with open(file, 'r') as f:
            self.open_file = f
            self.recursive_fun()
            self.open_file = None
        print('===============================')

    def get_line(self):
        self.rollback_addr = self.open_file.tell()
        self.line = self.open_file.readline().replace('\n', '')

    def recursive_call(self):
        self.open_file.seek(self.rollback_addr)
        self.recursive_fun()

    def check_start_node(self):
        if '+-o' not in self.line:
            logger.error('This is not normal. Recursive function called on random line.')
            exit(1)

    def not_empty_node_check(self):
        if not self.rollback_addr:
            logger.error("+-o in two consecutive lines, not supposed to be possible")
            exit(1)

    def iterate_children(self, depth):
        while self.line and (self.line[depth] == '|' or self.line[depth: depth+3] == '+-o'):
            if self.line[depth: depth+3] == '+-o':
                self.recursive_call()

            else:
                self.get_line()

    def fetch_node_data(self):
        while '+-o' not in self.line:
            if not self.line:
                return False # end of file
            
            node_data = [] # array of lines, to be transformed in json
            node_data.append(self.line)
            self.get_line()

        return True
    
    def recursive_fun(self):
        is_leaf = False
        self.get_line()

        # check if we're at the start of a node
        self.check_start_node()

        node_name = self.line.split("+-o")[1].strip()
        print("Node : ", node_name)
        depth = self.line.index('o') # to identify the other nodes that have the same parent
        self.get_line()

        # check if its a leaf
        if self.line[depth] != '|':
            is_leaf = True

        # Fetch the data of the node
        if not self.fetch_node_data():
            return  # EOF

        # stop if we're a leaf
        if is_leaf:
            self.open_file.seek(self.rollback_addr)
            return
            
        # sanity check
        self.not_empty_node_check()

        # going back one line to retrieve the node title line
        self.recursive_call()
        self.get_line()

        # Iterates over each child to call the current function
        self.iterate_children(depth)
        
        


