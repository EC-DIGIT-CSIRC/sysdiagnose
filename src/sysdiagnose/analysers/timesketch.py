#! /usr/bin/env python3
#
# For Python3
# Script to extract timestamp and generate a timesketch output
# 
# Version: 2025-04-08 -- hackathlon.lu
# Fixing issue 122
#
# Note:
#  Timesketch format:
# https://timesketch.org/guides/user/import-from-json-csv/
# Mandatory: timestamps must be in microseconds !!!
#   
# Example message:
#   {"message": "A message",
#    "timestamp": 123456789,
#    "datetime": "2015-07-24T19:01:01+00:00",
#    "timestamp_desc": "Write time",
#    "extra_field_1": "foo"}
#
# TODO: support merging of multiple fields for
#  - accessibility_tccs

from sysdiagnose.utils.base import BaseAnalyserInterface, logger
from sysdiagnose.utils.base import BaseParserInterface
import importlib

# Keys that are always present in parser outputs
default_keys = ["timestamp", "datetime"]


# Map specific keys from parser to expected Timesketch key
# For each parser: parser key -> timesketch key 
# MANDATORY: message and timestamp_desc
# OPTIONAL: extra_field_1
specific_keys = {
    "accessibility_tcc": [ # need to be extended
        ["service", "message"],
        ["client", "timestamp_desc"],
    ],
    "mobileinstallation": [
        ["message", "message"],
        ["event_type", "timestamp_desc"],
    ],
    "olddsc": [
        ["Path", "message"],
        ["UUID_String", "timestamp_desc"],
        ["Segments", "extra_field_1"],
    ],
    #"powerlogs": [ # need to be extended, fields are dynamic
    #    ["interface", "message"],
    #    ["module_name", "timestamp_desc"],
    #    #["down bytes", "extra_field_1"],
    #    #["up bytes", "extra_field_2"],
    #],
    "ps": [
        ["command", "message"],
        ["user", "timestamp_desc"],
    ],
    "security_sysdiagnose": [ # need to be extended
        ["result", "message"],
        ["event", "timestamp_desc"],
        ["attributes", "extra_field_1"],
    ],
    "shutdownlogs": [ # need to be extended
        ["path", "message"],
        ["uuid", "timestamp_desc"],
        ["event", "extra_field_1"],
    ],
    #"spindumpnosymbols": [ # requires a dedicated function/parser
    #    ["path", "message"],
    #    ["uuid", "timestamp_desc"],
    #    ["event", "extra_field_1"],
    #],
    "swcutil": [
        ["section", "message"],
        ["process", "timestamp_desc"],
        ["usage", "extra_field_1"],
    ],
    "sys": [
        ["BuildID", "message"],
        ["SystemImageID", "timestamp_desc"],
    ],
    "taskinfo": [
        ["datetime_description", "message"],
        ["tasks", "timestamp_desc"],
    ],
    "transparency": [
        ["message", "message"],
        ["message", "timestamp_desc"],
    ],
    "mobileactivation": [
        ["message", "message"],
        ["event_type", "timestamp_desc"],
    ],
}

class TimesketchAnalyser(BaseAnalyserInterface):
    description = 'Generate a Timesketch compatible timeline'
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)


    def get_timesketch_timeline(self):
        # will contain the timesketch timeline
        timesketch_timeline = []

        for parser_name in self.config.get_parsers():
            module = importlib.import_module(f'sysdiagnose.parsers.{parser_name}')

            # figure out the class name
            obj = None
            parser = None
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, BaseParserInterface) and obj is not BaseParserInterface:
                    parser: BaseParserInterface = obj(config=self.config, case_id=self.case_id)
                    if parser.contains_timestamp():
                        # check if there is a configuration for the parser
                        if parser_name not in specific_keys.keys():
                            logger.error("%s not supported for timesketch analyser" % parser_name)
                            continue
                        
                        result = parser.get_result()
                        # adapt parser result to timesketch format
                        for line in result:
                            timesketch_entry = timesketch  = {k: v for k, v in line.items() if k in ['timestamp', 'datetime']}
                            for pair in specific_keys[parser_name]:
                                key, value = pair
                                if key in line.keys():
                                    timesketch_entry[value] = line[key]
                                    timesketch_timeline.append(timesketch_entry)
                                else:
                                    logger.error("Missing key %s in %s from parser %s" % (key, line, parser_name))
                                    continue
        return timesketch_timeline   


    def execute(self):
        """
        This method is responsible for executing the functionality of the class.

        Load parsers here, and use the parser.get_result() to get the data.
        By doing so you will get the parser output even if it never ran before.
        """
        try:
            timesketch = self.get_timesketch_timeline()
            return timesketch
        except Exception as e:
            print(e)
            logger.exception("[ERROR] failed to create timesketch timeline")
        return []
