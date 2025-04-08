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


# Keep the following keys for each parser
# specific_keys = {
#     "accessibility_tcc": ["service", "client", "allowed", "auth"], # need to be extended
#     "mobileinstallation": ["message", "event_type"],
#     "olddsc": ["Path", "UUID_String", "Segments"],
#     "powerlogs": ["interface", "module_name", "down bytes", "up bytes"],     # need to be extended, fields are dynamic
#     "ps": ["command", "user"],
#     "security_sysdiagnose": ["result", "event", "attributes"], # need to be extended
#     "shutdownlogs": ["path", "uuid", "event"], # need to be extended
#     "spindumpnosymbols": ["path", "uuid", "event"], # need to be extended
#     "swcutil": [ "section", "process", "usage"],
#     "sys": ["BuildID", "SystemImageID"],
#     "taskinfo": ["datetime_description", "tasks"],
#     "transparency": ["message"],
#     "mobileactivation": ["message", "event_type"],
# }

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
                        #if parser_name not in specific_keys.keys():
                        #    logger.error("%s not supported for timesketch analyser" % parser_name)
                        #    continue
                        
                        result = parser.get_result()
                        # adapt parser result to timesketch format
                        for line in result:
                            try:
                                if not isinstance(line, dict):
                                    continue
                                if all(item in line.keys() for item in ['timestamp', 'datetime']):
                                    timesketch_entry =  {k: v for k, v in line.items() if k in ['timestamp', 'datetime']}
                                    message = {k: v for k, v in line.items() if k not in ["timestamp", "datetime"]}
                                    timesketch_entry["timestamp_desc"] = parser_name
                                    timesketch_entry["message"] = message
                                    timesketch_timeline.append(timesketch_entry)
                            except Exception as e:
                                logger.exception("[%s] - Failed to handle line: %s" % (parser_name, line))
                                continue

                            # Generate the message
                            #message = {}
                            #for key in specific_keys[parser_name]:
                            #    if key in line.keys():
                            #        message[key] = line[key]
                            #    else:
                            #        logger.debug("Parser: %s - available keys: %s" % (parser_name, line.keys()))
                            
                            
                            # Add the message to the timesketch entry
                            
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
