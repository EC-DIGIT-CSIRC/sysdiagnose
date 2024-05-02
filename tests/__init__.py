import unittest
import os
import glob


class SysdiagnoseTestCase(unittest.TestCase):

    def setUp(self):
        # find all folders such as
        # - testdata/iOSxx/sysdiagnose_YYYY.MM.DD_HH-MM-SS-SSSS_...
        # - testdata-private/iOSxx/sysdiagnose_YYYY.MM.DD_HH-MM-SS-SSSS_...
        # this allows testing locally with more data, while keeping online tests coherent

        self.log_root_paths = [name for name in glob.glob('tests/testdata*/**/sysdiagnose_*', recursive=True) if os.path.isdir(name)]
