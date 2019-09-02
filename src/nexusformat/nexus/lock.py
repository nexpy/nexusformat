import errno
import os
import time
import timeit

import six

if six.PY2:
    FileNotFoundError = IOError


class NXLockException(Exception):
    LOCK_FAILED = 1


class NXLock(object):

    def __init__(self, filename, timeout=60, check_interval=1):
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
        self.pid = os.getpid()
        self.fd = None

    def __repr__(self):
        return "NXLock('"+os.path.basename(self.filename)+"', pid="+ str(self.pid)+")"

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
                self.fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                open(self.lock_file, 'w').write(str(self.pid))
                break
            except OSError as e:
                # Only catch if the lockfile already exists
                if e.errno != errno.EEXIST:
                    raise
                time.sleep(check_interval)
        # Raise on error if we had to wait for too long
        else:
            raise NXLockException("'%s' is currently locked by an external process" 
                                  % self.filename)

    def release(self):
        """Release the lock."""
        if self.fd is not None:
            os.close(self.fd)
            try:
                os.remove(self.lock_file)
            except FileNotFoundError:
                pass
            self.fd = None

    def clear(self):
        """Clear the lock even if created by another process."""
        if self.fd is not None:
            self.release()
        else:
            try:
                os.remove(self.lock_file)
            except FileNotFoundError:
                pass
            self.fd = None

    def wait(self, timeout=None, check_interval=None):
        """Wait until an existing lock is cleared.
        
        This is for use in processes checking for external locks.
        
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
            If lock not cleared before `timeout`.
        """
        if timeout is None:
            timeout = self.timeout 
        if check_interval is None:
            check_interval = self.check_interval
        timeoutend = timeit.default_timer() + timeout
        while timeoutend > timeit.default_timer():
            if not os.path.exists(self.lock_file):
                break
            time.sleep(check_interval)
        else:
            raise NXLockException("'%s' is currently locked by an external process" 
                                  % self.lock_file)
        return        

    def __enter__(self):
        return self.acquire()

    def __exit__(self, type_, value, tb):
        self.release()

    def __del__(self):
        self.release()
