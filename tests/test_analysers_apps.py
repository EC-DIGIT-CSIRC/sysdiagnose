from analysers.apps import analyse_path
from parsers import accessibility_tcc, brctl, itunesstore, logarchive
from tests import SysdiagnoseTestCase
import unittest
import os
import tempfile


class TestAnalysersApps(SysdiagnoseTestCase):

    def test_analyse_apps(self):
        for log_root_path in self.log_root_paths:

            with tempfile.TemporaryDirectory() as tmp_outpath:
                # first run the parsers
                accessibility_tcc.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                brctl.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                itunesstore.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                logarchive.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)

                # then run the analyser
                output_file = os.path.join(tmp_outpath, 'apps.json')
                analyse_path(case_folder=tmp_outpath, output_file=output_file)
                self.assertTrue(os.path.isfile(output_file))


if __name__ == '__main__':
    unittest.main()
