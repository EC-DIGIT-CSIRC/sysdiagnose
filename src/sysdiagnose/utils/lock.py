

import time
from pathlib import Path


class FileLock:
    '''
    A simple lock implementation using a file-based approach.

    It creases a file {filename}.lock in the same directory as the file
    to be locked. The lock is released when the file is deleted.
    This is useful for ensuring that only one process can access a resource at a time.

    Make sure to use try, finally and always release the lock.
    '''
    @staticmethod
    def acquire_lock(filename: str, timeout: int = 5):
        """Create a lock file for the given filename, waiting for the lock to be available."""
        lock_file = Path(f"{filename}.lock")
        start_time = time.time()

        while lock_file.exists():
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Could not acquire lock for {filename} within {timeout} seconds.")
            time.sleep(0.1)

        lock_file.touch()

    @staticmethod
    def release_lock(filename: str):
        """Release the lock by deleting the lock file."""
        lock_file = Path(f"{filename}.lock")
        if lock_file.exists():
            lock_file.unlink()
