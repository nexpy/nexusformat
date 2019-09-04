import os
import pytest
from nexusformat.nexus import *


field1 = NXfield('a', name="f1")


def test_lock_creation(tmpdir):

    filename = os.path.join(tmpdir, 'file1.nxs')
    root = NXroot(NXentry(field1))
    root.save(filename)

    assert root.nxfile.lock is None

    root.nxfile.lock = 20
    root.nxfile.acquire_lock()
    root.nxfile.release_lock()

    assert not root.nxfile.locked
    assert not root.nxfile.is_locked()

    root.nxfile.lock = True
    root.nxfile.acquire_lock()

    assert root.nxfile.locked
    assert root.nxfile.is_locked()
    assert root.nxfile.lock.timeout == 10

    root['entry/f1'] = 'b'

    assert root['entry/f1'] == 'b'
    
    assert not root.nxfile.locked
    assert not root.nxfile.is_locked()


def test_locked_assignments(tmpdir):

    filename = os.path.join(tmpdir, 'file1.nxs')
    root = NXroot(NXentry(field1))
    root.save(filename)
    assert root.nxfile.lock is None

    original_id = id(root.nxfile)
    original_mtime = root._mtime

    root['entry/f1'] = 'b'

    assert root['entry/f1'] == 'b'
    assert root.nxfile.lock is None
    
    root.nxfile.lock = 10

    assert isinstance(root.nxfile.lock, NXLock)
    assert root.nxfile.lock.timeout == 10

    root['entry/f1'] = 'c'

    assert root['entry/f1'] == 'c'
    assert id(root.nxfile) == original_id
    assert root._mtime > original_mtime


