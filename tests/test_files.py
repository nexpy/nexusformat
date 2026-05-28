import os

import numpy as np
import pytest
from nexusformat.nexus.tree import (NXdata, NXentry, NXfield, NXFile, NXroot,
                                    nxload, nxopen)


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


def test_read_lazy_field_after_same_path_rewrap(tmpdir):
    """A file-backed NXfield that has been deep-copied into a new
    in-memory container at the same on-disk path used to raise
    ``RuntimeError: destination object already exists`` when read,
    because ``_get_uncopied_data`` asked HDF5 to copy the field onto
    itself. This is the scenario hit by the nexpy PlotDialog when a
    field inside an NXdata is selected as the signal: the dialog
    wraps it in a fresh NXdata with the same name and reparents to
    the original grandparent, so the wrapped field's nxpath collides
    with the source. The field must be large enough to stay
    lazy-loaded (``_value is None``) so the deepcopy preserves the
    ``_uncopied_data`` reference.
    """
    filename = os.path.join(tmpdir, "file.nxs")
    shape = (2000, 2000)  # big enough to stay lazy-loaded
    root = NXroot(NXentry(NXdata(
        NXfield(np.zeros(shape, dtype=np.int64), name="signal"),
        name="data")))
    root["entry/data/signal_mask"] = NXfield(np.zeros(shape, dtype=bool))
    root["entry/data/signal"].attrs["mask"] = "signal_mask"
    root.save(filename, mode="w")
    del root

    root = nxload(filename, "rw")
    src = root["entry/data"]
    # Mimic PlotDialog: wrap the mask in a new NXdata named after the
    # original group, reparented to the entry. The wrapped field
    # ends up at /entry/data/signal_mask -- the same path as the
    # source.
    wrapper = NXdata(src["signal_mask"], name=src.nxname)
    wrapper.nxgroup = src.nxgroup
    field = wrapper.nxsignal
    assert field._uncopied_data is not None
    assert field._uncopied_data[1] == field.nxpath

    arr = field[()]
    assert arr.shape == shape
    assert arr.dtype == bool
    assert field._uncopied_data is None
