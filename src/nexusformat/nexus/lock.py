import os
import time, timeit
import errno


class NXLockException(Exception):
    LOCK_FAILED = 1

class NXLock(object):

    def __init__(self, filename, timeout=600, check_interval=1):
        """Create a lock to prevent file access.

        This creates a lock, which can be later acquired and released. It
        creates a file, named `<filename>.lock`, which contains the 
        calling process ID. 
        
        Parameters
        ----------
        filename : str
            Name of file to be locked.
        timeout : int, optional
            Number of seconds to wait for a prior lock to clear before 
            raising a NXLockException, by default 600.
        check_interval : int, optional
            Number of seconds between attempts to acquire the lock, 
            by default 1.
        """
        self.filename = os.path.realpath(filename)
        self.lock_file = self.filename+'.lock'
        self.timeout = timeout
        self.check_interval = check_interval
        self.fd = None

    def acquire(self, timeout=None, check_interval=None):
        """Acquire the lock.
        
        Parameters
        ----------
        timeout : int, optional
            Number of seconds to wait for a prior lock to clear before 
            raising a NXLockException, by default `self.timeout`.
        check_interval : int, optional
            Number of seconds between attempts to acquire the lock, 
            by default `self.check_interval`.
        
        Raises
        ------
        NXLockException
            If lock not acquired before `timeout`.
        """
        if timeout is None:
            timeout = self.timeout
        if timeout is None:
            timeout = 0

        if check_interval is None:
            check_interval = self.check_interval

        timeoutend = timeit.default_timer() + timeout
        while timeoutend > timeit.default_timer():
            try:
                # Attempt to create the lockfile. If it already exists,
                # then someone else has the lock and we need to wait
                self.fd = os.open(self.lock_file,
                        os.O_CREAT | os.O_EXCL | os.O_RDWR)
                open(self.lock_file, 'w').write(str(os.getpid()))
                break
            except OSError as e:
                # Only catch if the lockfile already exists
                if e.errno != errno.EEXIST:
                    raise
                time.sleep(check_interval)
        # Raise on error if we had to wait for too long
        else:
            raise NXLockException("'%s' timeout expired" % self.filename)

    def release(self):
        """Release the lock."""
        if self.fd is not None:
            os.close(self.fd)
            try:
                os.remove(self.lock_file)
            except FileNotFoundError:
                pass
            self.fd = None

    def __enter__(self):
        return self.acquire()

    def __exit__(self, type_, value, tb):
        self.release()

    def __del__(self):
        self.release()
