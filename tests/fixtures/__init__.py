"""
Self-contained parser/analyser fixtures used by the test suite.

These replicate the behavior of the former ``demo_parser`` / ``demo_analyser``
reference modules (which now live under ``docs/samples/`` and are intentionally
outside the importable package). Keeping them here decouples the test suite from
any shipped module: tests can exercise summary round-trips and iOS-version
gating against a known-good subject without depending on discoverable code.
"""

from tests.fixtures.sample_analyser import SampleAnalyser
from tests.fixtures.sample_parser import SampleParser

__all__ = ["SampleAnalyser", "SampleParser"]
