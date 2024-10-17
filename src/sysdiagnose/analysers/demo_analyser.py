#! /usr/bin/env python3

# For Python3
# DEMO - Skeleton

from sysdiagnose.utils.base import BaseAnalyserInterface, logger


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
        try:
            print("DO SOMETHING HERE")
            logger.info("log something here", extra={'analyser': __name__})
            if True:
                logger.warning("This will log a warning")
                # logger.error("This will log an error")

            # json_data = p_fooparser.get_result()
        except Exception as e:
            logger.exception("This will log an error with the exception information")
            # logger.warning("This will log a warning with the exception information", exc_info=True)

        result = {'foo': 'bar'}
        return result
