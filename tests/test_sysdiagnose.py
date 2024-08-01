from tests import SysdiagnoseTestCase
import sysdiagnose
import unittest
import config


class TestSysdiagnose(SysdiagnoseTestCase):

    def test_get_case_ids(self):
        config.cases = {
            '1': {
                'case_id': 1,
                'source_file': 'sysdiagnose_file',
                'source_sha256': 'readable_hash',
                'case_file': 'case_file',
                'serial_number': 'serial_number',
                'unique_device_id': 'unique_device_id'
            },
            '2': {
                'case_id': 2,
                'source_file': 'sysdiagnose_file',
                'source_sha256': 'readable_hash',
                'case_file': 'case_file',
                'serial_number': 'serial_number',
                'unique_device_id': 'unique_device_id'
            },
            'foo': {
                'case_id': 'foo',
                'source_file': 'sysdiagnose_file',
                'source_sha256': 'readable_hash',
                'case_file': 'case_file',
                'serial_number': 'serial_number',
                'unique_device_id': 'unique_device_id'
            }
        }
        ids = sysdiagnose.get_case_ids()
        self.assertListEqual(ids, ['1', '2', 'foo'])


if __name__ == '__main__':
    unittest.main()
