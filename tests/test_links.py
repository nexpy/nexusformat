import os

import numpy as np
import pytest
from nexusformat.nexus.tree import (NXentry, NXfield, NXgroup, NXlink, NXroot,
                                    nxload, nxsetlock)


@pytest.fixture
def field1a(): return NXfield((1, 2), name="f1", dtype=np.float32, units='m')
@pytest.fixture
def field2a(): return NXfield((3, 4), name="f2", dtype=np.int16)


def test_link_creation(field1a):

    root = NXroot()
    root["g1"] = NXgroup(f1=field1a)
    root["g2"] = NXgroup()
    root["g2"].f1_link = NXlink(root["g1/f1"])

    assert "g1/f1" in root
    assert "g2/f1_link" in root
    assert root["g2/f1_link"].nxlink == root["g1/f1"]
    assert root["g2/f1_link"].nxtarget == "/g1/f1"

    root["g2/f2_link"] = NXlink(target="/g1/f1")

    assert root["g2/f2_link"].nxlink == root["g1/f1"]

    root["g2"].makelink(root["g1/f1"], name="f3_link")
    assert root["g2/f3_link"].nxlink == root["g1/f1"]


@pytest.mark.parametrize("save", ["False", "True"])
def test_saved_links(tmpdir, field1a, save):

    root = NXroot()
    root["g1"] = NXgroup(f1=field1a)
    root["g2"] = NXgroup()

    filename = os.path.join(tmpdir, "file1.nxs")
    root.save(filename, mode="w")

    root["g2"].f1_link = NXlink(root["g1/f1"])

    if save:
        root = nxload(filename, "rw")

    assert root["g2/f1_link"].shape == (2,)
    assert root["g2/f1_link"].dtype == np.float32

    root["g1/f1"].attrs["a1"] = 1

    assert "a1" in root["g2/f1_link"].attrs
    assert root["g2/f1_link"].a1 == 1

    assert root["g2/f1_link"].nxdata[0] == root["g1/f1"].nxdata[0]


@pytest.mark.parametrize("save", ["False", "True"])
def test_linkfield_properties(tmpdir, field1a, save):

    root = NXroot()
    root["g1"] = NXgroup(f1=field1a)
    root["g2"] = NXgroup()
    root["g2"].f1_link = NXlink(root["g1/f1"])

    if save:
        filename = os.path.join(tmpdir, "file1.nxs")
        root.save(filename, mode="w")

    assert root["g2/f1_link"].shape == (2,)
    assert root["g2/f1_link"].dtype == np.float32

    root["g1/f1"].attrs["a1"] = 1

    assert "a1" in root["g2/f1_link"].attrs
    assert root["g2/f1_link"].a1 == 1

    assert root["g2/f1_link"].nxdata[0] == root["g1/f1"].nxdata[0]


@pytest.mark.parametrize("save", ["False", "True"])
def test_linkgroup_properties(tmpdir, field1a, save):

    root = NXroot(NXentry())
    root["entry/g1"] = NXgroup()
    root["entry/g1/g2"] = NXgroup(field1a)
    root["entry/g2_link"] = NXlink("entry/g1/g2")

    if save:
        filename = os.path.join(tmpdir, "file1.nxs")
        root.save(filename, mode="w")
        root = nxload(filename)

    assert "f1" in root["entry/g2_link"]
    assert len(root["entry/g2_link"]) == len(root["entry/g1/g2"])
    assert root["entry/g2_link"].nxtarget == "/entry/g1/g2"
    assert root["entry/g1/g2/f1"].nxroot is root
    assert root["entry/g1/g2/f1"].nxgroup is root["entry/g2_link"].nxlink
    assert root["entry/g2_link"].nxroot is root
    assert root["entry/g2_link"].nxgroup is root["entry"]
    assert root["entry/g2_link"].nxlink.entries == root["entry/g1/g2"].entries


@pytest.mark.parametrize("save", ["False", "True"])
def test_embedded_links(tmpdir, save, field1a, field2a):

    root = NXroot(NXentry())
    root["entry/g1"] = NXgroup()
    root["entry/g1/g2"] = NXgroup()
    root["entry/g1/g2/g3"] = NXgroup(field1a)
    root["entry/g2_link"] = NXlink("entry/g1/g2")

    if save:
        filename = os.path.join(tmpdir, "file1.nxs")
        root.save(filename, mode="w")
        root = nxload(filename, "rw")

    assert "f1" in root["entry/g2_link/g3"]
    assert not root["entry/g2_link"].is_linked()
    assert root["entry/g2_link/g3"].is_linked()
    assert root["entry/g2_link/g3/f1"].is_linked()
    assert len(root["entry/g2_link/g3"]) == len(root["entry/g1/g2/g3"])
    assert root["entry/g2_link/g3/f1"].nxpath == "/entry/g2_link/g3/f1"
    assert root["entry/g2_link/g3/f1"].nxfilepath == "/entry/g1/g2/g3/f1"
    assert root["entry/g2_link/g3/f1"].nxroot is root
    assert root["entry/g2_link/g3/f1"].nxgroup.nxgroup is root["entry/g2_link"]

    root["entry/g1/g2/g3/f1"] = [7, 8]
    root["entry/g1/g2/g3/f1"].attrs["a"] = 1

    assert root["entry/g2_link/g3/f1"][0] == 7
    assert "a" in root["entry/g2_link/g3/f1"].attrs
    assert root["entry/g2_link/g3/f1"].attrs["a"] == 1

    root["entry/g1/g2/g3/f2"] = field2a

    assert "f2" in root["entry/g2_link/g3"]

    del root["entry/g1/g2/g3/f2"]

    assert "f2" not in root["entry/g2_link/g3"]


@pytest.mark.parametrize("save", ["False", "True"])
def test_external_field_links(tmpdir, field1a, save):

    root = NXroot(NXentry())

    if save:
        filename = os.path.join(tmpdir, "file1.nxs")
        root.save(filename, mode="w")

    external_filename = os.path.join(tmpdir, "file2.nxs")
    external_root = NXroot(NXentry(field1a))
    external_root.save(external_filename, mode="w")

    root["entry/f1_link"] = NXlink(target="/entry/f1", file=external_filename)

    assert root["entry/f1_link"].nxtarget == "/entry/f1"
    assert root["entry/f1_link"].nxfilepath == "/entry/f1"
    assert root["entry/f1_link"].nxfilename == external_filename
    assert root["entry/f1_link"].nxfilemode == "r"
    assert root["entry/f1_link"].nxroot == root
    assert root["entry/f1_link"].nxgroup == root["entry"]

    assert root["entry/f1_link"].file_exists()
    assert root["entry/f1_link"].path_exists()
    assert root["entry/f1_link"].shape == external_root["entry/f1"].shape
    assert root["entry/f1_link"][0] == external_root["entry/f1"][0]
    assert "units" in root["entry/f1_link"].attrs


@pytest.mark.parametrize("save", ["False", "True"])
def test_external_group_links(tmpdir, field1a, save):

    root = NXroot(NXentry())

    if save:
        filename = os.path.join(tmpdir, "file1.nxs")
        root.save(filename, mode="w")

    external_filename = os.path.join(tmpdir, "file2.nxs")
    external_root = NXroot(
        NXentry(NXgroup(field1a, name='g1', attrs={"a": "b"})))
    external_root.save(external_filename, mode="w")

    root["entry/g1_link"] = NXlink(target="/entry/g1", file=external_filename)

    assert root["entry/g1_link"].nxtarget == "/entry/g1"
    assert root["entry/g1_link"].nxfilepath == "/entry/g1"
    assert root["entry/g1_link"].nxfilename == external_filename
    assert root["entry/g1_link"].nxfilemode == "r"
    assert root["entry/g1_link"].nxroot == root
    assert root["entry/g1_link"].nxgroup == root["entry"]
    assert root["entry/g1_link"].file_exists()
    assert root["entry/g1_link"].path_exists()

    assert "f1" in root["entry/g1_link"]
    assert root["entry/g1_link/f1"].nxfilename == (
        root["entry/g1_link"].nxfilename)
    assert root["entry/g1_link/f1"].nxfilepath == "/entry/g1/f1"
    assert root["entry/g1_link/f1"].nxroot == root
    assert root["entry/g1_link/f1"].nxgroup is root["entry/g1_link"]
    assert root["entry/g1_link/f1"][0] == external_root["entry/g1/f1"][0]

    assert "a" in root["entry/g1_link"].attrs
    assert "units" in root["entry/g1_link/f1"].attrs


def test_external_group_files(tmpdir, field1a):

    nxsetlock(10)

    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry())
    root.save(filename, mode="w")

    external_filename = os.path.join(tmpdir, "file2.nxs")
    external_root = NXroot(
        NXentry(NXgroup(field1a, name='g1', attrs={"a": "b"})))
    external_root.save(external_filename, mode="w")

    root["entry/g1_link"] = NXlink(target="/entry/g1", file=external_filename)
    with root.nxfile:

        assert root.nxfile.filename == filename
        assert root.nxfile.locked

        with root["entry/g1_link"].nxfile:

            assert root["entry/g1_link"].nxfile.filename == external_filename
            assert root["entry/g1_link"].nxfile.locked

        assert root.nxfile.locked
        assert not root["entry/g1_link"].nxfile.locked

    assert not root.nxfile.locked

@pytest.mark.parametrize("save", ["False", "True"])
def test_soft_field_links(tmpdir, field1a, field2a,save):

    root = NXroot()
    root["g1"] = NXgroup()
    root["g1/g2"] = NXgroup(f1=field1a, f2=field2a)
    root["g1"].f1_link = NXlink(target="g2/f1", soft=True)
    root["g1"].f2_link = NXlink(target="g1/g2/f2", soft=True)

    if save:
        filename = os.path.join(tmpdir, "file1.nxs")
        root.save(filename, mode="w")

    assert root["g1/f1_link"].shape == (2,)
    assert root["g1/f1_link"].dtype == np.float32

    root["g1/g2/f1"].attrs["a1"] = 1

    assert "a1" in root["g1/f1_link"].attrs
    assert root["g1/f1_link"].a1 == 1

    assert root["g1/f1_link"].nxdata[0] == root["g1/g2/f1"].nxdata[0]

    assert root["g1/f2_link"].shape == (2,)
    assert root["g1/f2_link"].dtype == np.int16

    root["g1/g2/f2"].attrs["a2"] = 2

    assert "a2" in root["g1/f2_link"].attrs
    assert root["g1/f2_link"].a2 == 2

    assert root["g1/f2_link"].nxdata[0] == root["g1/g2/f2"].nxdata[0]
