#! /usr/bin/env python3

# For Python3
# DEMO - Skeleton

from sysdiagnose.utils.base import BaseAnalyserInterface


class DemoAnalyser(BaseAnalyserInterface):
    description = "Do something useful (DEMO)"
    # format = "json"  # by default json

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def execute(self):
        """
        This method is responsible for executing the functionality of the class.

        Load parsers here, and use the parser.get_result() to get the data.
        By doing so you will get the parser output even if it never ran before.
        """
        print("DO SOMETHING HERE")

        # json_data = p_fooparser.get_result()

        result = {'foo': 'bar'}
        return result
