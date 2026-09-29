"""
Minimal analyser fixture for the test suite.

Behaves exactly like the former ``demo_analyser``: it returns ``{"foo": "bar"}``
and logs one warning plus one error, producing a summary with status ERROR,
num_events=1, num_warnings=1, num_errors=1.
"""

from sysdiagnose.utils.base import BaseAnalyserInterface, SysdiagnoseConfig, logger


class SampleAnalyser(BaseAnalyserInterface):
    description = "Sample analyser (test fixture)"
    # format defaults to "json"; ios_version defaults to "*".

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def execute(self):
        logger.info("Sample analyser running")
        logger.warning("This will log a warning")
        logger.error("This will log an error")
        return {"foo": "bar"}
