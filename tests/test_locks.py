import os
import time

import pytest
from nexusformat.nexus.tree import (NeXusError, NXentry, NXLock, NXroot,
                                    nxload, nxsetconfig, text)


def test_lock_creation(tmpdir, field4):

    nxsetconfig(lock=0)
    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry(field4))
    root.save(filename)

    assert root.nxfile.lock is not None

    root.nxfile.acquire_lock()

    assert not root.nxfile.locked
    assert not root.nxfile.is_locked()

    root.nxfile.release_lock()

    assert not root.nxfile.locked
    assert not root.nxfile.is_locked()

    root.nxfile.lock = True
    root.nxfile.acquire_lock()

    assert root.nxfile.locked
    assert root.nxfile.is_locked()
    assert root.nxfile.lock.timeout == 10

    root["entry/f1"] = "b"

    assert root["entry/f1"] == "b"

    assert not root.nxfile.locked
    assert not root.nxfile.is_locked()


def test_locked_assignments(tmpdir, field4):

    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry(field4))
    root.save(filename)

    assert root.nxfile.mtime == os.path.getmtime(filename)

    original_id = id(root.nxfile)
    originalmtime = root.mtime

    root["entry/f1"] = "b"

    assert root["entry/f1"] == "b"

    root.nxfile.lock = 10

    assert isinstance(root.nxfile.lock, NXLock)
    assert root.nxfile.lock.timeout == 10

    time.sleep(0.1)

    root["entry/f1"] = "c"

    assert root["entry/f1"] == "c"
    assert id(root.nxfile) == original_id
    assert root.mtime > originalmtime


def test_lock_interactions(tmpdir, field4):

    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry(field4))
    root.save(filename)

    assert not root.nxfile.is_open()

    root1 = nxload(filename, mode="rw")
    root2 = nxload(filename, mode="r")

    time.sleep(0.1)

    root1.nxfile.lock = 10
    root1["entry/f1"] = "b"

    assert root1.mtime > root2.mtime


def test_lock_defaults(tmpdir, field4):

    nxsetconfig(lock=20)
    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry(field4))
    root.save(filename, "w")

    with root.nxfile as f:

        assert isinstance(root.nxfile.lock, NXLock)
        assert root.nxfile.lock.timeout == 20
        assert root.nxfile.locked
        assert root.nxfile.is_locked()

    assert not root.nxfile.locked
    assert not root.nxfile.is_locked()

    nxsetconfig(lock=0)
    root = NXroot(NXentry(field4))
    root.save(filename, "w")

    with root.nxfile as f:

        assert not root.nxfile.locked
        assert not root.nxfile.is_locked()


def test_nested_locks(tmpdir, field4):

    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry(field4))
    root.save(filename, "w")
    root.nxfile.lock = True

    assert isinstance(root.nxfile.lock, NXLock)

    with root.nxfile:

        assert root.nxfile.locked
        assert root.nxfile.is_locked()

        root["entry/f1"] = "b"

        assert text(root.nxfile["entry/f1"][()]) == "b"

        with root.nxfile:

            root["entry/f1"] = "c"

            assert text(root.nxfile["entry/f1"][()]) == "c"
            assert root.nxfile.locked
            assert root.nxfile.is_locked()

        assert root.nxfile.locked
        assert root.nxfile.is_locked()

    assert not root.nxfile.locked
    assert not root.nxfile.is_locked()


def test_stale_locks(tmpdir):

    nxsetconfig(lock=2, lockexpiry=3600)
    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry())
    root.save(filename, "w")

    with open(root.nxfile.lock_file, 'w'):
        os.utime(root.nxfile.lock_file, None)

    assert os.path.exists(root.nxfile.lock_file)

    with pytest.raises(NeXusError):
        root.nxfile.acquire_lock()

    assert not root.nxfile.locked
    assert root.nxfile.is_locked()

    stat = os.stat(root.nxfile.lock_file)
    os.utime(root.nxfile.lock_file, (stat.st_atime, stat.st_mtime - 10000))

    with root.nxfile:

        assert root.nxfile.locked
        assert root.nxfile.is_locked()

    assert not root.nxfile.locked
    assert not root.nxfile.is_locked()
