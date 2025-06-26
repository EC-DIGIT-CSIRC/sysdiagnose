from tests import SysdiagnoseTestCase
from sysdiagnose import Sysdiagnose
import unittest
import tempfile
import shutil
import glob
import os
import tarfile


class TestSysdiagnose(SysdiagnoseTestCase):

    def test_get_case_ids(self):
        sd = Sysdiagnose()
        sd._cases = {
            '1': {
                'case_id': 1,
                'source_file': 'sysdiagnose_file',
                'source_sha256': 'readable_hash',
                'serial_number': 'serial_number',
                'unique_device_id': 'unique_device_id'
            },
            '2': {
                'case_id': 2,
                'source_file': 'sysdiagnose_file',
                'source_sha256': 'readable_hash',
                'serial_number': 'serial_number',
                'unique_device_id': 'unique_device_id'
            },
            'foo': {
                'case_id': 'foo',
                'source_file': 'sysdiagnose_file',
                'source_sha256': 'readable_hash',
                'serial_number': 'serial_number',
                'unique_device_id': 'unique_device_id'
            }
        }
        ids = sd.get_case_ids()
        self.assertListEqual(ids, ['1', '2', 'foo'])

    def test_create_case(self):
        # Create a temporary directory
        try:
            temp_dir = tempfile.mkdtemp()
            sd = Sysdiagnose(cases_path=temp_dir)
            # take the first sysdiagnose tar archive that's there and try it out
            sd_archive_files = [name for name in glob.glob('tests/testdata*/**/*.tar.gz', recursive=True)]
            for archive_file in sd_archive_files:
                print(f"Creating case from {archive_file}")
                sd.create_case(archive_file)
                break

        finally:
            # Ensure the temporary directory is cleaned up after the test
            shutil.rmtree(temp_dir)

    def test_create_case_from_folder(self):
        # Create a temporary directory
        # take the first sysdiagnose tar archive that's there and try it out
        try:
            temp_dir = tempfile.mkdtemp()
            sd = Sysdiagnose(cases_path=temp_dir)
            for name in glob.glob('tests/testdata*/**/*.tar.gz', recursive=True):
                with tarfile.open(name) as tf:
                    tf.extractall(temp_dir)

                archive_folder = glob.glob(os.path.join(temp_dir, '*')).pop()
                sd.create_case(archive_folder)
                break

        finally:
            # Ensure the temporary directory is cleaned up after the test
            shutil.rmtree(temp_dir)

    def test_init_case_logging(self):
        try:
            temp_dir = tempfile.mkdtemp()
            sd = Sysdiagnose(cases_path=temp_dir)
            sd.init_case_logging(mode='parse', case_id='1')
            self.assertTrue(os.path.exists(os.path.join(sd.config.get_case_log_data_folder('1'), 'log-parse.jsonl')))
        finally:
            # Ensure the temporary directory is cleaned up after the test
            shutil.rmtree(temp_dir)

    def test_case_metadata_remotectl(self):
        # check if the metadata is correct
        expected_metadata = {
            'serial_number': 'F4GT2K24HG7K',
            'unique_device_id': 'e22f7f830e5dcc1287a1690a2622c2b12afaa33c',
            'ios_version': '15.7.6',
            'model': 'iPhone9,3',
            'date': '2023-05-24T20:29:15.000000+00:00',
            'case_id': 'F4GT2K24HG7K_20230524_202915',
            'source_file': 'tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349.tar.gz',
            'source_sha256': '870dc007c0ee7b04960e6e88c1d25c11461b0f1f5fba0914a1d2a7947045dbf2',
        }
        metadata = Sysdiagnose.get_case_metadata('tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349.tar.gz')
        self.assertEqual(metadata, expected_metadata)

        # check signature
        expected_hash = '870dc007c0ee7b04960e6e88c1d25c11461b0f1f5fba0914a1d2a7947045dbf2'
        hash = Sysdiagnose.calculate_metadata_signature(metadata)
        self.assertEqual(hash, expected_hash)

    # def test_cases_metadata(self):
    #     for case_id, case in self.sd.cases().items():
    #         metadata = self.sd.get_case_metadata(case['source_file'])

    #         self.assertTrue(metadata['case_id'].startswith(case_id))


if __name__ == '__main__':
    unittest.main()
