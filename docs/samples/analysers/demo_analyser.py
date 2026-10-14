#! /usr/bin/env python3

# ---------------------------------------------------------------------------
# REFERENCE SAMPLE — NOT part of the sysdiagnose package.
#
# This file is intentionally kept outside of `src/sysdiagnose/analysers/` so it
# is NOT discovered by the framework, exposed via the CLI, packaged in the
# wheel, or picked up by the test suite. It exists purely as a starting point
# for developers writing a new analyser.
#
# To turn it into a real analyser: copy it into `src/sysdiagnose/analysers/`,
# rename the class, and implement `execute()`.
# See docs/developer_guidelines.md for the full contract.
# ---------------------------------------------------------------------------

from sysdiagnose.utils.base import BaseAnalyserInterface, SysdiagnoseConfig, logger


class DemoAnalyser(BaseAnalyserInterface):
    description = "Do something useful (DEMO)"
    # format = "json"  # by default json
    # ios_version = ">=17.0"  # optional: PEP 440 specifier for compatible iOS versions (default: "*" = all)

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def execute(self):
        """
        This method is responsible for executing the functionality of the class.

        Load parsers here, and use the parser.get_result() to get the data.
        By doing so you will get the parser output even if it never ran before.

        Note: pass self.case to dependent parsers to propagate case metadata.
        """
        try:
            logger.info("DO SOMETHING HERE")
            logger.info("log something here", extra={"field1": "field1_info_details"})
            logger.debug("log something for debugging purposes", extra={"field1": "field1_debug_details"})
            if True:
                logger.warning("This will log a warning")
                logger.error("This will log an error")

            # Example: load a parser's result
            # from sysdiagnose.parsers.my_parser import MyParser
            # json_data = MyParser(self.config, self.case).get_result()
        except Exception:
            logger.exception("This will log an error with the exception information")
            logger.warning("This will log a warning with the exception information", exc_info=True)

        result = {"foo": "bar"}
        return result
