import os
import unittest

from sysdiagnose.utils.base import BaseParserInterface
from tests import SysdiagnoseTestCase


class _ExplodingParser(BaseParserInterface):
    """Yields a couple of good events, then fails part-way through the write."""

    description = "test parser that fails during write"
    format = "jsonl"
    module_name = "exploding"

    def get_log_files(self) -> list:
        return []

    def execute(self):
        def _gen():
            yield {"message": "one", "datetime": "2023-05-24T13:29:15+00:00", "timestamp_desc": "t", "module": "e"}
            yield {"message": "two", "datetime": "2023-05-24T13:29:16+00:00", "timestamp_desc": "t", "module": "e"}
            raise RuntimeError("disk full")

        return _gen()


class TestBaseWriteFailure(SysdiagnoseTestCase):
    def test_partial_write_is_not_served_as_a_cached_result(self):
        case = {"case_id": "base-write-failure", "ios_version": "16.0"}
        p = _ExplodingParser(__file__, self.sd.config, case=case)

        result, summary = p._execute_and_write()

        # the truncated output file must be gone, so output_exists() cannot serve it as a cache
        self.assertFalse(os.path.exists(p.output_file))
        self.assertFalse(p.output_exists())
        # the failure must be recorded, not reported as a clean empty run
        # >= 1: the logged exception is also counted by the attached ResultSummaryLogHandler
        self.assertGreaterEqual(summary.num_errors, 1)
        self.assertEqual(0, summary.num_events)
        self.assertEqual([], result)


if __name__ == "__main__":
    unittest.main()
