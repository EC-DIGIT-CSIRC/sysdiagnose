import unittest

from sysdiagnose.utils.base import BaseParserInterface
from tests import SysdiagnoseTestCase


class _NoOpParser(BaseParserInterface):
    """Minimal parser used to exercise BaseInterface.case_model."""

    description = "test parser for case_model"
    format = "jsonl"
    module_name = "case_model_probe"

    def get_log_files(self) -> list:
        return []

    def execute(self):
        return []


class TestBaseCaseModel(SysdiagnoseTestCase):
    def _make(self, case: dict) -> _NoOpParser:
        return _NoOpParser(__file__, self.sd.config, case=case)

    def test_returns_model_when_present(self):
        p = self._make({"case_id": "case-model-present", "model": "iPad16,3"})
        self.assertEqual("iPad16,3", p.case_model)

    def test_returns_unknown_when_missing(self):
        p = self._make({"case_id": "case-model-missing"})
        self.assertEqual("unknown", p.case_model)

    def test_returns_unknown_when_none(self):
        p = self._make({"case_id": "case-model-none", "model": None})
        self.assertEqual("unknown", p.case_model)

    def test_returns_unknown_when_empty_string(self):
        p = self._make({"case_id": "case-model-empty", "model": ""})
        self.assertEqual("unknown", p.case_model)

    def test_is_always_str_and_safe_for_membership_checks(self):
        # The whole point of the contract: consumers can do "X" not in self.case_model
        # without guarding against None.
        for case in (
            {"case_id": "c1", "model": "AppleTV11,1"},
            {"case_id": "c2"},
            {"case_id": "c3", "model": None},
        ):
            with self.subTest(case_id=case["case_id"]):
                p = self._make(case)
                self.assertIsInstance(p.case_model, str)
                # must not raise TypeError
                _ = "AppleTV" not in p.case_model


if __name__ == "__main__":
    unittest.main()
