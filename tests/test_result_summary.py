import os
import unittest
from datetime import datetime

from sysdiagnose.analysers.demo_analyser import DemoAnalyser
from sysdiagnose.parsers.demo_parser import DemoParser
from sysdiagnose.utils.base import ExecutionStatus
from tests import SysdiagnoseTestCase


class TestResultSummary(SysdiagnoseTestCase):
    def test_demo_parser_summary_roundtrip(self):
        case_id = self.sd.get_case_ids()[0]

        parser = DemoParser(self.sd.config, case_id=case_id)
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

        cached_parser = DemoParser(self.sd.config, case_id=case_id)
        result = cached_parser.get_result()
        self.assertEqual(len(result), 1)

        cached_summary = cached_parser.get_result_summary()
        self.assertEqual(cached_summary.status, ExecutionStatus.WARNING)
        self.assertEqual(cached_summary.num_warnings, 1)
        self.assertIsInstance(cached_summary.start_time, datetime)
        self.assertIsNotNone(cached_summary.duration)

    def test_demo_parser_summary_fallback_without_sidecar(self):
        case_id = self.sd.get_case_ids()[0]

        parser = DemoParser(self.sd.config, case_id=case_id)
        parser.save_result(force=True)
        os.remove(parser.summary_file)

        cached_parser = DemoParser(self.sd.config, case_id=case_id)
        result = cached_parser.get_result()
        self.assertEqual(len(result), 1)

        summary = cached_parser.get_result_summary()
        self.assertEqual(summary.status, ExecutionStatus.OK)
        self.assertEqual(summary.num_errors, 0)
        self.assertEqual(summary.num_warnings, 0)
        self.assertEqual(summary.num_events, 1)
        self.assertIsNone(summary.start_time)
        self.assertIsNone(summary.duration)

    def test_demo_analyser_summary_roundtrip(self):
        case_id = self.sd.get_case_ids()[0]

        analyser = DemoAnalyser(self.sd.config, case_id=case_id)
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

        cached_analyser = DemoAnalyser(self.sd.config, case_id=case_id)
        result = cached_analyser.get_result()
        self.assertEqual(result, {"foo": "bar"})

        cached_summary = cached_analyser.get_result_summary()
        self.assertEqual(cached_summary.status, ExecutionStatus.ERROR)
        self.assertEqual(cached_summary.num_errors, 1)
        self.assertEqual(cached_summary.num_warnings, 1)
        self.assertIsInstance(cached_summary.start_time, datetime)
        self.assertIsNotNone(cached_summary.duration)


if __name__ == '__main__':
    unittest.main()
