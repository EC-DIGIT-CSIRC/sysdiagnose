import unittest
from unittest.mock import MagicMock, patch

from sysdiagnose.utils.summary import ExecutionStatus, ResultSummary


def _ok_summary():
    s = ResultSummary(status=ExecutionStatus.SUCCESS, num_events=1)
    s.duration = 0.0
    return s


class TestMainCrashIsolation(unittest.TestCase):
    """One crashing parser/analyser must not abort the remaining ones or the remaining cases."""

    def _run_main(self, mode, attr, names):
        attempted = []

        def _side_effect(name, case_id):
            attempted.append((name, case_id))
            if name == names[0]:
                raise ValueError("boom")
            return _ok_summary()

        sd = MagicMock()
        sd.config.get_parsers.return_value = dict.fromkeys(names)
        sd.config.get_analysers.return_value = dict.fromkeys(names)
        sd.get_case_ids.return_value = ["case1", "case2"]
        setattr(sd, attr, MagicMock(side_effect=_side_effect))

        argv = ["sysdiagnose", "-c", "all", mode, "all"]
        with (
            patch("sysdiagnose.__main__.Sysdiagnose", return_value=sd),
            patch("sysdiagnose.__main__.sys.argv", argv),
            patch("sysdiagnose.__main__.case_csv_to_case_ids", return_value=["case1", "case2"]),
        ):
            from sysdiagnose.__main__ import main

            main()
        return attempted

    def test_parse_continues_after_a_crashing_parser(self):
        attempted = self._run_main("parse", "parse", ["boom_parser", "good_parser"])
        # both parsers attempted, for both cases -- the crash did not abort the run
        self.assertEqual(
            [
                ("boom_parser", "case1"),
                ("good_parser", "case1"),
                ("boom_parser", "case2"),
                ("good_parser", "case2"),
            ],
            attempted,
        )

    def test_analyse_continues_after_a_crashing_analyser(self):
        attempted = self._run_main("analyse", "analyse", ["boom_analyser", "good_analyser"])
        self.assertEqual(
            [
                ("boom_analyser", "case1"),
                ("good_analyser", "case1"),
                ("boom_analyser", "case2"),
                ("good_analyser", "case2"),
            ],
            attempted,
        )


if __name__ == "__main__":
    unittest.main()
