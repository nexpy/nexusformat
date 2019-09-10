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
    """Class for acquiring and releasing file-based locks.
    
    Attributes
    ----------
    lock_file : str
        Name of the lock file. This has the extension `.lock` appended to 
        the name of the locked file.
    pid : int
        Current process id.
    fd : int
        File descriptor of the opened lock file.
    """

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

        if timeout == 0:
            return

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
        # Raise an error if we had to wait for too long
        else:
            raise NXLockException("'%s' is currently locked by an external process" 
                                  % self.filename)

    def release(self):
        """Release the lock.
        
        Note
        ====
        This will only work if the lock was created by the current process.
        """
        if self.fd is not None:
            os.close(self.fd)
            try:
                os.remove(self.lock_file)
            except FileNotFoundError:
                pass
            self.fd = None
 
    @property
    def locked(self):
        """Return True if the current process has locked the file."""
        return self.fd is not None

    def clear(self):
        """Clear the lock even if created by another process.
        
        This will either release a lock created by the current process or
        remove the lock file created by an external process.

        Note
        ====
        This is used to clear stale locks caused by a process that terminated
        prematurely. It should be used with caution.

        """
        if self.fd is not None:
            self.release()
        else:
            try:
                os.remove(self.lock_file)
            except FileNotFoundError:
                pass

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
        if os.path.exists(self.lock_file):
            if timeout is None:
                timeout = self.timeout 
            if check_interval is None:
                check_interval = self.check_interval
            timeoutend = timeit.default_timer() + timeout
            while timeoutend > timeit.default_timer():
                time.sleep(check_interval)
                if not os.path.exists(self.lock_file):
                    break
            else:
                raise NXLockException("'%s' is currently locked by an external process" 
                                      % self.filename)
        return        

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *args):
        self.release()

    def __del__(self):
        self.release()
