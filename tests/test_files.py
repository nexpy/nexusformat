import os

import numpy as np
import pytest
from nexusformat.nexus.tree import (NXdata, NXentry, NXfield, NXFile, NXgroup,
                                    NXroot, nxload, nxopen)


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


def test_read_lazy_field_on_copy(tmpdir):

    filename = os.path.join(tmpdir, "file.nxs")
    shape = (2000, 2000)
    root = NXroot(NXentry(NXdata(
        NXfield(np.zeros(shape, dtype=np.int64), name="signal"),
        name="data")))
    root["entry/data/signal_mask"] = NXfield(np.zeros(shape, dtype=bool))
    root["entry/data/signal"].attrs["mask"] = "signal_mask"
    root.save(filename, mode="w")
    del root

    root = nxload(filename, "rw")
    src = root["entry/data"]
    wrapper = NXdata(src["signal_mask"], name=src.nxname)
    wrapper.nxgroup = src.nxgroup
    field = wrapper.nxsignal
    assert field._uncopied_data is not None
    assert field._uncopied_data[1] == field.nxpath

    arr = field[()]
    assert arr.shape == shape
    assert arr.dtype == bool
    assert field._uncopied_data is None


@pytest.mark.parametrize("nested", [False, True])
def test_copy_group_materializes_owned_fields(tmp_path, nested):

    values = np.arange(10001, dtype=np.int32)
    source = NXroot(NXentry(NXgroup(name="data")))
    parent = "entry/data"
    if nested:
        source[parent + "/nested"] = NXgroup()
        parent += "/nested"
    source[parent + "/counts"] = NXfield(values, units="counts")
    filename = tmp_path / "source.nxs"
    source.save(filename)
    source.close()
    source = nxload(filename)
    assert source[parent + "/counts"]._value is None

    destination = NXroot(NXentry())
    destination["entry/copied"] = source["entry/data"]
    field_path = "entry/copied/" + ("nested/" if nested else "") + "counts"
    field = destination[field_path]
    assert field._uncopied_data is None
    assert field._memfile is not None
    source.close()
    filename.rename(tmp_path / "renamed-source.nxs")
    np.testing.assert_array_equal(field.nxdata, values)
    assert field.units == "counts"
    destination.save(tmp_path / "copied.nxs")
    destination.close()
    reopened = nxload(tmp_path / "copied.nxs")
    np.testing.assert_array_equal(reopened[field_path].nxdata, values)
    reopened.close()
