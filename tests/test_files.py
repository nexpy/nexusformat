import numpy as np
import os
import pytest
import six
from nexusformat.nexus import *

field1 = NXfield((1,2), name="f1")
field2 = NXfield((3,4), name="f2")
field3 = NXfield((5,6), name="f3")


def test_file_creation(tmpdir):

    filename = os.path.join(tmpdir, "file.nxs")
    with NXFile(filename, "w") as f:
        assert f.mode == "rw"
        assert f.filename == filename
    assert not f.is_open()


def test_file_save(tmpdir):

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
def test_file_recursion(tmpdir, recursive):

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
        

