import os
import tempfile
import unittest

from sysdiagnose import Sysdiagnose


class TestCaseMetadataFallback(unittest.TestCase):
    """
    get_case_metadata() must not raise when remotectl_dumpstate.txt is missing or unparseable.

    On main, `remotectl_dumpstate_json` and `sysdiagnose_date_utc` are only bound inside the try
    block, but are read unconditionally after it -- so any failure there raises UnboundLocalError
    and the documented ioreg/SystemVersion fallback below can never execute.
    """

    def test_missing_remotectl_dumpstate_does_not_raise(self):
        with tempfile.TemporaryDirectory() as folder:
            # a sysdiagnose folder with neither remotectl_dumpstate.txt nor a readable sysdiagnose.log
            metadata = Sysdiagnose.get_case_metadata(folder)
        self.assertIsNone(metadata)

    def test_unparseable_remotectl_dumpstate_does_not_raise(self):
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, "sysdiagnose.log"), "w") as f:
                f.write("not a real sysdiagnose log\n")
            with open(os.path.join(folder, "remotectl_dumpstate.txt"), "w") as f:
                f.write("garbage\n")
            metadata = Sysdiagnose.get_case_metadata(folder)
        self.assertIsNone(metadata)


if __name__ == "__main__":
    unittest.main()
