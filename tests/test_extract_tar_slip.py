import io
import os
import tarfile
import tempfile
import unittest

from sysdiagnose import Sysdiagnose


def _add_file(tf: tarfile.TarFile, name: str, content: bytes = b"payload\n") -> None:
    info = tarfile.TarInfo(name)
    info.size = len(content)
    tf.addfile(info, io.BytesIO(content))


def _add_symlink(tf: tarfile.TarFile, name: str, target: str) -> None:
    info = tarfile.TarInfo(name)
    info.type = tarfile.SYMTYPE
    info.linkname = target
    tf.addfile(info)


class TestExtractTarSlip(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.sd = Sysdiagnose(cases_path=os.path.join(self.root, "cases"))
        # same layout create_case() uses: <cases>/<case_id>/data
        self.destination = self.sd.config.get_case_data_folder("case1")

    def tearDown(self):
        self._tmp.cleanup()

    def _archive(self, build) -> str:
        path = os.path.join(self.root, f"archive-{len(os.listdir(self.root))}.tar.gz")
        with tarfile.open(path, "w:gz") as tf:
            build(tf)
        return path

    def _malicious_archives(self) -> dict:
        def traversal(tf):
            _add_file(tf, "good.txt")
            _add_file(tf, "../../ESCAPED.txt")

        def absolute(tf):
            _add_file(tf, os.path.join(self.root, "ABSOLUTE.txt"))

        def symlink_escape(tf):
            _add_symlink(tf, "link", "../../..")
            _add_file(tf, "link/VIA_LINK.txt")

        def absolute_symlink(tf):
            _add_symlink(tf, "abs", self.root)
            _add_file(tf, "abs/VIA_ABS_LINK.txt")

        def device(tf):
            info = tarfile.TarInfo("fifo")
            info.type = tarfile.FIFOTYPE
            tf.addfile(info)

        return {
            "traversal": (self._archive(traversal), os.path.join(self.root, "cases", "ESCAPED.txt")),
            "absolute": (self._archive(absolute), os.path.join(self.root, "ABSOLUTE.txt")),
            "symlink_escape": (self._archive(symlink_escape), os.path.join(self.root, "VIA_LINK.txt")),
            "absolute_symlink": (self._archive(absolute_symlink), os.path.join(self.root, "VIA_ABS_LINK.txt")),
            "device": (self._archive(device), None),
        }

    def _assert_rejected(self):
        for label, (archive, escaped_path) in self._malicious_archives().items():
            with self.subTest(archive=label):
                raised = False
                try:
                    self.sd.extract_sysdiagnose_files(archive, self.destination)
                except Exception:
                    raised = True
                if escaped_path:
                    self.assertFalse(os.path.exists(escaped_path), f"{label}: wrote {escaped_path}")
                if label != "absolute":
                    # the "data" filter re-roots a leading "/" inside the destination rather than failing
                    self.assertTrue(raised, f"{label}: archive was not rejected")

    def _assert_benign_archive_extracts(self):
        def benign(tf):
            _add_file(tf, "sysdiagnose_x/sysdiagnose.log")
            _add_symlink(tf, "sysdiagnose_x/alias.log", "sysdiagnose.log")

        self.sd.extract_sysdiagnose_files(self._archive(benign), self.destination)
        log = os.path.join(self.destination, "sysdiagnose_x", "sysdiagnose.log")
        self.assertTrue(os.path.isfile(log))
        self.assertTrue(os.path.islink(os.path.join(self.destination, "sysdiagnose_x", "alias.log")))

    def test_malicious_members_are_rejected(self):
        self._assert_rejected()

    def test_benign_archive_extracts(self):
        self._assert_benign_archive_extracts()


if __name__ == "__main__":
    unittest.main()
