import os
import pytest
import time
from nexusformat.nexus import *
from nexusformat.nexus.tree import text

field1 = NXfield("a", name="f1")


def test_lock_creation(tmpdir):

    nxsetlock(0)
    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry(field1))
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


def test_locked_assignments(tmpdir):

    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry(field1))
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


def test_lock_interactions(tmpdir):

    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry(field1))
    root.save(filename)

    assert not root.nxfile.is_open()

    root1 = nxload(filename, mode="rw")
    root2 = nxload(filename, mode="r")

    time.sleep(0.1)

    root1.nxfile.lock = 10
    root1["entry/f1"] = "b"

    assert root1.mtime > root2.mtime


def test_lock_defaults(tmpdir):  

    nxsetlock(20)
    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry(field1))
    root.save(filename, "w")

    with root.nxfile as f:

        assert isinstance(root.nxfile.lock, NXLock)
        assert root.nxfile.lock.timeout == 20
        assert root.nxfile.locked
        assert root.nxfile.is_locked()    

    assert not root.nxfile.locked
    assert not root.nxfile.is_locked()

    nxsetlock(0)
    root = NXroot(NXentry(field1))
    root.save(filename, "w")

    with root.nxfile as f:

        assert not root.nxfile.locked
        assert not root.nxfile.is_locked()


def test_nested_locks(tmpdir):

    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry(field1))
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
