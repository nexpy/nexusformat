# -----------------------------------------------------------------------------
# Copyright (c) 2019-2021, NeXpy Development Team.
#
# Author: Paul Kienzle, Ray Osborn
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------

"""Module to provide a file locking mechanism to prevent data corruption."""

import errno
import os
import socket
import time
import timeit
from pathlib import Path


class NXLockException(Exception):
    LOCK_FAILED = 1


class NXLock:
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

    def __init__(self, filename, timeout=None, check_interval=1, expiry=28800,
                 directory=None):
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
            raising a NXLockException, by default 60.
        check_interval : int, optional
            Number of seconds between attempts to acquire the lock,
            by default 1.
        expiry : int, optional
            Number of seconds after which a lock expires, by default 8*3600.
            Set to 0 or None to make the locks persist indefinitely.
        directory : str, optional
            Path to directory to contain lock file paths.
        """
        from .tree import nxgetconfig

        self.filename = Path(filename).resolve()
        suffix = self.filename.suffix + '.lock'
        if timeout is None:
            timeout = nxgetconfig('lock')
        self.timeout = timeout
        self.check_interval = check_interval
        self.expiry = expiry
        if directory is None:
            directory = nxgetconfig('lockdirectory')
        if directory:
            try:
                directory = Path(directory).resolve(strict=True)
            except FileNotFoundError:
                raise NXLockException(
                    f"Lockfile directory '{directory}' does not exist")
            path = self.filename.relative_to(self.filename.anchor)
            self.lock_file = Path(directory).joinpath('!!'.join(path.parts)
                                                      ).with_suffix(suffix)
        else:
            self.lock_file = self.filename.with_suffix(suffix)
        self.pid = os.getpid()
        self.addr = f"{self.pid}@{socket.gethostname}"
        self.fd = None

    def __repr__(self):
        return f"NXLock('{self.filename.name}', pid={self.addr})"

    def acquire(self, timeout=None, check_interval=None, expiry=None):
        """Acquire the lock.

        Parameters
        ----------
        timeout : int, optional
            Number of seconds to wait for a prior lock to clear before
            raising a NXLockException, by default `self.timeout`.
        check_interval : int, optional
            Number of seconds between attempts to acquire the lock,
            by default `self.check_interval`.
        expiry : int, optional
            Number of seconds after which a lock expires, by default
            `self.expiry`.

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

        if expiry is None:
            expiry = self.expiry

        timeoutend = timeit.default_timer() + timeout
        initial_attempt = True
        while timeoutend > timeit.default_timer():
            try:
                # Attempt to create the lockfile. If it already exists,
                # then someone else has the lock and we need to wait
                self.fd = os.open(self.lock_file,
                                  os.O_CREAT | os.O_EXCL | os.O_RDWR)
                open(self.lock_file, 'w').write(self.addr)
                os.chmod(self.lock_file, 0o777)
                break
            except OSError as e:
                # Only catch if the lockfile already exists
                if e.errno != errno.EEXIST:
                    raise
                # Remove the lockfile if it is older than one day
                elif initial_attempt and expiry:
                    if self.is_stale(expiry=expiry):
                        self.clear()
                    initial_attempt = False
                time.sleep(check_interval)
        # Raise an error if we had to wait for too long
        else:
            self.fd = None
            raise NXLockException(
                f"'{self.filename}' is currently locked by an external process"
                )

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
        if not self.lock_file.exists():
            self.fd = None
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
        if self.lock_file.exists():
            if timeout is None:
                timeout = self.timeout
            if check_interval is None:
                check_interval = self.check_interval
            timeoutend = timeit.default_timer() + timeout
            while timeoutend > timeit.default_timer():
                time.sleep(check_interval)
                if not self.lock_file.exists():
                    break
            else:
                raise NXLockException(f"'{self.filename}' is currently locked "
                                      "by an external process")
        return

    def is_stale(self, expiry=None):
        """Return True if the lock file is older than one day.

        If the lock file has been cleared before this check, the
        function returns False to enable another attempt to acquire it.
        """
        if expiry is None:
            expiry = self.expiry
        try:
            return ((time.time() - self.lock_file.stat().st_mtime) > expiry)
        except FileNotFoundError:
            return False

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *args):
        self.release()

    def __del__(self):
        self.release()
