import os
import unittest
from datetime import datetime

from sysdiagnose.utils.summary import ExecutionStatus
from tests import SysdiagnoseTestCase
from tests.fixtures import SampleAnalyser, SampleParser


class TestResultSummary(SysdiagnoseTestCase):
    def test_parser_summary_roundtrip(self):
        _case = next(iter(self.sd.cases().values()))

        parser = SampleParser(self.sd.config, case=_case)
        parser.save_result(force=True)

        self.assertTrue(os.path.isfile(parser.summary_file))

        summary = parser.get_result_summary()
        self.assertEqual(summary.status, ExecutionStatus.WARNING)
        self.assertEqual(summary.num_errors, 0)
        self.assertEqual(summary.num_warnings, 1)
        self.assertEqual(summary.num_events, 1)
        self.assertIsInstance(summary.start_time, datetime)
        self.assertIsNotNone(summary.duration)
        self.assertGreaterEqual(summary.duration, 0)

        cached_parser = SampleParser(self.sd.config, case=_case)
        result = cached_parser.get_result()
        self.assertEqual(len(result), 1)

        cached_summary = cached_parser.get_result_summary()
        self.assertEqual(cached_summary.status, ExecutionStatus.WARNING)
        self.assertEqual(cached_summary.num_warnings, 1)
        self.assertIsInstance(cached_summary.start_time, datetime)
        self.assertIsNotNone(cached_summary.duration)

    def test_parser_summary_fallback_without_sidecar(self):
        _case = next(iter(self.sd.cases().values()))

        parser = SampleParser(self.sd.config, case=_case)
        parser.save_result(force=True)
        os.remove(parser.summary_file)

        cached_parser = SampleParser(self.sd.config, case=_case)
        result = cached_parser.get_result()
        self.assertEqual(len(result), 1)

        summary = cached_parser.get_result_summary()
        self.assertEqual(summary.status, ExecutionStatus.ERROR)
        self.assertEqual(summary.num_errors, 0)
        self.assertEqual(summary.num_warnings, 0)
        self.assertEqual(summary.num_events, 0)
        self.assertIsNone(summary.start_time)
        self.assertIsNone(summary.duration)

    def test_analyser_summary_roundtrip(self):
        _case = next(iter(self.sd.cases().values()))

        analyser = SampleAnalyser(self.sd.config, case=_case)
        analyser.save_result(force=True)

        self.assertTrue(os.path.isfile(analyser.output_file))
        self.assertTrue(os.path.isfile(analyser.summary_file))

        summary = analyser.get_result_summary()
        self.assertEqual(summary.status, ExecutionStatus.ERROR)
        self.assertEqual(summary.num_errors, 1)
        self.assertEqual(summary.num_warnings, 1)
        self.assertEqual(summary.num_events, 1)
        self.assertIsInstance(summary.start_time, datetime)
        self.assertIsNotNone(summary.duration)

        cached_analyser = SampleAnalyser(self.sd.config, case=_case)
        result = cached_analyser.get_result()
        self.assertEqual(result, {"foo": "bar"})

        cached_summary = cached_analyser.get_result_summary()
        self.assertEqual(cached_summary.status, ExecutionStatus.ERROR)
        self.assertEqual(cached_summary.num_errors, 1)
        self.assertEqual(cached_summary.num_warnings, 1)
        self.assertIsInstance(cached_summary.start_time, datetime)
        self.assertIsNotNone(cached_summary.duration)


if __name__ == "__main__":
    unittest.main()
