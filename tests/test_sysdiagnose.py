import glob
import json
import os
import shutil
import tarfile
import tempfile
import unittest

from sysdiagnose import Sysdiagnose
from tests import SysdiagnoseTestCase


class TestSysdiagnose(SysdiagnoseTestCase):
    def test_get_case_ids(self):
        sd = Sysdiagnose()
        sd._cases = {
            "1": {
                "case_id": 1,
                "source_file": "sysdiagnose_file",
                "source_sha256": "readable_hash",
                "serial_number": "serial_number",
                "unique_device_id": "unique_device_id",
            },
            "2": {
                "case_id": 2,
                "source_file": "sysdiagnose_file",
                "source_sha256": "readable_hash",
                "serial_number": "serial_number",
                "unique_device_id": "unique_device_id",
            },
            "foo": {
                "case_id": "foo",
                "source_file": "sysdiagnose_file",
                "source_sha256": "readable_hash",
                "serial_number": "serial_number",
                "unique_device_id": "unique_device_id",
            },
        }
        ids = sd.get_case_ids()
        self.assertListEqual(ids, ["1", "2", "foo"])

    def test_create_case(self):
        # Create a temporary directory
        try:
            temp_dir = tempfile.mkdtemp()
            sd = Sysdiagnose(cases_path=temp_dir)
            # take the first sysdiagnose tar archive that's there and try it out
            sd_archive_files = list(glob.glob("tests/testdata*/**/*.tar.gz", recursive=True))
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
            for name in glob.glob("tests/testdata*/**/*.tar.gz", recursive=True):
                with tarfile.open(name) as tf:
                    tf.extractall(temp_dir)

                archive_folder = glob.glob(os.path.join(temp_dir, "*")).pop()
                sd.create_case(archive_folder)
                break

        finally:
            # Ensure the temporary directory is cleaned up after the test
            shutil.rmtree(temp_dir)

    def test_read_only_use_creates_no_cases_folder(self):
        # Instantiating Sysdiagnose and listing cases in a directory without any
        # cases must not create the cases folder or cases.json on disk.
        try:
            temp_dir = tempfile.mkdtemp()
            cases_path = os.path.join(temp_dir, "cases")
            sd = Sysdiagnose(cases_path=cases_path)
            self.assertFalse(os.path.exists(cases_path), "cases folder should not be created on instantiation")

            self.assertEqual(sd.cases(), {})
            self.assertEqual(sd.get_case_ids(), [])

            self.assertFalse(os.path.exists(cases_path), "cases folder should not be created by read-only use")
            self.assertFalse(os.path.exists(os.path.join(cases_path, "cases.json")))
        finally:
            shutil.rmtree(temp_dir)

    def test_create_two_cases_keeps_cases_json_valid(self):
        # Regression test: creating a second case must overwrite cases.json, not
        # append a second JSON object to it (which corrupts the file).
        try:
            temp_dir = tempfile.mkdtemp()
            cases_path = os.path.join(temp_dir, "cases")
            sd = Sysdiagnose(cases_path=cases_path)

            archives = sorted(glob.glob("tests/testdata*/**/*.tar.gz", recursive=True))[:2]
            self.assertEqual(len(archives), 2, "need at least two test archives for this test")

            sd.create_case(archives[0], case_id="one")
            sd.create_case(archives[1], case_id="two")

            # cases.json must still be valid JSON and contain both cases.
            with open(os.path.join(cases_path, "cases.json")) as f:
                data = json.load(f)
            self.assertEqual(sorted(data.keys()), ["one", "two"])

            # A fresh instance must read both cases back.
            sd2 = Sysdiagnose(cases_path=cases_path)
            self.assertEqual(sorted(sd2.get_case_ids()), ["one", "two"])
        finally:
            shutil.rmtree(temp_dir)

    def test_init_case_logging(self):
        try:
            temp_dir = tempfile.mkdtemp()
            sd = Sysdiagnose(cases_path=temp_dir)
            sd.init_case_logging(mode="parse", case_id="1")
            self.assertTrue(os.path.exists(os.path.join(sd.config.get_case_log_data_folder("1"), "log-parse.jsonl")))
        finally:
            # Ensure the temporary directory is cleaned up after the test
            shutil.rmtree(temp_dir)

    def test_case_metadata_remotectl(self):
        # check if the metadata is correct
        expected_metadata = {
            "serial_number": "F4GT2K24HG7K",
            "unique_device_id": "e22f7f830e5dcc1287a1690a2622c2b12afaa33c",
            "ios_version": "15.7.6",
            "model": "iPhone9,3",
            "date": "2023-05-24T20:29:15.000000+00:00",
            "case_id": "F4GT2K24HG7K_20230524_202915",
            "source_file": "tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349.tar.gz",
            "source_sha256": "870dc007c0ee7b04960e6e88c1d25c11461b0f1f5fba0914a1d2a7947045dbf2",
        }
        metadata = Sysdiagnose.get_case_metadata(
            "tests/testdata/iOS15/sysdiagnose_2023.05.24_13-29-15-0700_iPhone-OS_iPhone_19H349.tar.gz"
        )
        self.assertEqual(metadata, expected_metadata)

        # check signature
        expected_hash = "870dc007c0ee7b04960e6e88c1d25c11461b0f1f5fba0914a1d2a7947045dbf2"
        hash = Sysdiagnose.calculate_metadata_signature(metadata)
        self.assertEqual(hash, expected_hash)


if __name__ == "__main__":
    unittest.main()
