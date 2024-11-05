from tests import SysdiagnoseTestCase
from sysdiagnose import Sysdiagnose
import unittest
import tempfile
import shutil
import glob


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


if __name__ == '__main__':
    unittest.main()
