
from tests import SysdiagnoseTestCase
from sysdiagnose.utils.lock import FileLock
import unittest


class TestMisc(SysdiagnoseTestCase):

    def test_lock(self):
        lock = FileLock('foo.txt', timeout=1)
        # first remove any existing lock file
        lock.lock_file.unlink(missing_ok=True)
        # do the real test
        lock.acquire()
        self.assertTrue(lock.locked)
        lock.release()
        self.assertFalse(lock.locked)
        self.assertFalse(lock.lock_file.exists())

    def test_lock_timeout(self):
        lock = FileLock('foo.txt', timeout=1)
        # first remove any existing lock file
        lock.lock_file.unlink(missing_ok=True)
        lock.acquire()
        self.assertTrue(lock.locked)

        # Try to acquire the lock again, should raise TimeoutError
        with self.assertRaises(TimeoutError):
            lock2 = FileLock('foo.txt', timeout=1)
            lock2.acquire()

        # Release the first lock
        lock.release()
        self.assertFalse(lock.locked)
        self.assertFalse(lock.lock_file.exists())

        # Now we can acquire the lock again
        lock2.acquire()
        self.assertTrue(lock2.locked)
        lock2.release()
        self.assertFalse(lock2.lock_file.exists())


if __name__ == '__main__':
    unittest.main()
