import os

import pytest
from nexusformat.nexus.tree import (NXdata, NXentry, NXFile, NXroot, nxload,
                                    nxopen)


def test_file_creation(tmpdir):

    filename = os.path.join(tmpdir, "file.nxs")
    with NXFile(filename, "w") as f:
        assert f.mode == "rw"
        assert f.filename == filename
    assert not f.is_open()


def test_file_save(tmpdir, field1, field2):

    filename = os.path.join(tmpdir, "file.nxs")

    w1 = NXroot(NXentry())
    w1.entry.data = NXdata(field1, field2)
    w1.save(filename)

    assert os.path.exists(filename)
    assert not w1.nxfile.is_open()
    assert w1.nxfilename == filename
    assert w1.nxfilemode == "rw"

    w2 = nxload(filename)
    assert w2.nxfilename == filename
    assert w2.nxfilemode == "r"
    assert "entry/data/f1" in w2
    assert "entry/data/f2" in w2
    assert "signal" in w2["entry/data"].attrs
    assert "axes" in w2["entry/data"].attrs


@pytest.mark.parametrize("recursive", ["True", "False"])
def test_file_recursion(tmpdir, field1, field2, recursive):

    filename = os.path.join(tmpdir, "file.nxs")
    w1 = NXroot(NXentry())
    w1.entry.data = NXdata(field1, field2)
    w1.save(filename)

    w2 = nxload(filename, recursive=recursive)

    if not recursive:
        assert w2["entry"]._entries is None
        assert "entry/data" in w2
        assert w2["entry"]._entries is not None
        assert w2["entry/data"]._entries is None
        assert "entry/data/f1" in w2
        assert w2["entry/data"]._entries is not None
        assert w2["entry/data/f2"] == field2

    assert "entry/data/f1" in w2
    assert "entry/data/f2" in w2
    assert "signal" in w2["entry/data"].attrs
    assert "axes" in w2["entry/data"].attrs


def test_file_context_manager(tmpdir, field1, field2):

    filename = os.path.join(tmpdir, "file.nxs")

    with nxopen(filename, "w") as w1:
        w1["entry"] = NXentry()
        w1["entry/data"] = NXdata(field1, field2)
        assert w1.nxfilename == filename
        assert w1.nxfilemode == "rw"

    assert os.path.exists(filename)

    w2 = nxopen(filename)
    assert w2.nxfilename == filename
    assert w2.nxfilemode == "r"
    assert "entry/data/f1" in w2
    assert "entry/data/f2" in w2
    assert "signal" in w2["entry/data"].attrs
    assert "axes" in w2["entry/data"].attrs
