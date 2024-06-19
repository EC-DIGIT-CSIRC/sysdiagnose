from analysers.timeliner import analyse_path
from parsers import accessibility_tcc, logarchive, mobileactivation, powerlogs, swcutil, shutdownlogs, wifisecurity, wifi_known_networks
from tests import SysdiagnoseTestCase
import unittest
import os
import tempfile


class TestAnalysersTimeliner(SysdiagnoseTestCase):

    def test_analyse_timeliner(self):
        for log_root_path in self.log_root_paths:

            with tempfile.TemporaryDirectory() as tmp_outpath:
                # first run the parsers
                accessibility_tcc.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                logarchive.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                mobileactivation.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                powerlogs.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                shutdownlogs.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                swcutil.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                wifi_known_networks.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)
                wifisecurity.parse_path_to_folder(log_root_path, output_folder=tmp_outpath)

                # then run the analyser
                output_file = os.path.join(tmp_outpath, 'timeliner.jsonl')
                analyse_path(case_folder=tmp_outpath, output_file=output_file)
                self.assertTrue(os.path.isfile(output_file))
                self.assertGreater(os.path.getsize(output_file), 0)


if __name__ == '__main__':
    unittest.main()
