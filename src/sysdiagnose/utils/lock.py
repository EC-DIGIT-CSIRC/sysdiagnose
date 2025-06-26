

import time
from pathlib import Path


class FileLock:
    '''
    A simple lock implementation using a file-based approach.

    It creases a file {filename}.lock in the same directory as the file
    to be locked. The lock is released when the file is deleted.
    This is useful for ensuring that only one process can access a resource at a time.

    Make sure to use try, finally and always release the lock if a lock was acquired.

    Usage:
    lock = FileLock("myfile.txt")
    try:
        lock.acquire()
        # Perform operations on the file
    except TimeoutError as e:
        print(f"Could not acquire lock: {e}")
    finally:
        lock.release()
    '''
    def __init__(self, filename: str, timeout: int = 5):
        self.filename = filename
        self.timeout = timeout
        self.locked = False
        self.lock_file = Path(f"{filename}.lock")

    def acquire(self):
        """
        Acquire the lock for the given filename.
        Waits until the lock is available or raises a TimeoutError if it cannot be acquired within the specified timeout.
        """
        if self.locked:
            return  # Already locked, no need to acquire again

        start_time = time.time()
        while self.lock_file.exists():
            if time.time() - start_time > self.timeout:
                self.locked = False
                raise TimeoutError(f"Could not acquire lock for {self.filename} within {self.timeout} seconds.")
            time.sleep(0.1)

        self.lock_file.touch()
        self.locked = True

    def release(self):
        """
        Release the lock by deleting the lock file.
        If the lock file does not exist, it does nothing.
        """
        if self.locked:
            self.locked = False
            if self.lock_file.exists():
                self.lock_file.unlink()
