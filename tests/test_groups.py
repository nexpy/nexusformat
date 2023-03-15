import os

from nexusformat.nexus.tree import NXdata, NXentry, NXgroup, NXlink, NXroot


def test_group_creation(field1, field2, field3):

    group1 = NXgroup(name="group")

    assert group1
    assert len(group1) == 0
    assert group1.nxname == "group"
    assert group1.nxgroup is None

    group2 = NXgroup(field1)

    assert group2
    assert len(group2) == 1
    assert "f1" in group2

    group1["f2"] = field2

    assert "f2" in group1

    group1["g2"] = group2

    assert len(group1) == 2
    assert "g2" in group1
    assert group1["g2/f1"] is group1.g2.f1

    group1["g2/f3"] = field3

    assert "f3" in group1["g2"]
    assert "g2/f3" in group1
    assert group1["g2/f3"].nxgroup == group1["g2"]

    group3 = NXgroup(g1=group1)

    assert "g1/g2/f1" in group3
    assert group3["g1"].nxgroup == group3


def test_group_entries(field1, field2, field3, field4, arr1D, arr2D):

    entries = {"f2": field2, "f3": arr1D, "s1": "string",
               "g1": NXgroup(field3)}

    group1 = NXgroup(field1, f4=field4, f5=arr2D, entries=entries)

    assert "f1" in group1
    assert "f2" in group1
    assert "f3" in group1
    assert "f4" in group1
    assert "f5" in group1
    assert "s1" in group1
    assert "g1" in group1
    assert "g1/f3" in group1

    assert group1["f1"] == field1
    assert group1["f2"] == field2
    assert group1["f3"].nxdata.sum() == arr1D.sum()
    assert group1["f4"].nxdata == field4.nxdata
    assert group1["f5"].nxdata.sum() == arr2D.sum()
    assert group1["s1"].nxdata == "string"
    assert group1["g1/f3"] == field3


def test_group_attrs():

    group1 = NXgroup(attrs={"a": "b", "c": 1})

    assert "a" in group1.attrs
    assert "c" in group1.attrs

    assert group1.attrs["a"] == "b"
    assert group1.attrs["c"] == 1


def test_group_insertion(field2):

    group1 = NXgroup()

    group1.insert(field2, name="f1")

    assert "f1" in group1
    assert len(group1) == 1


def test_group_rename(field1):

    group = NXgroup(field1)

    assert "f1" in group

    group["f1"].rename("f2")

    assert "f1" not in group
    assert "f2" in group


def test_entry_creation():

    group = NXentry()

    assert group.nxname == "entry"
    assert group.nxclass == "NXentry"
    assert isinstance(group, NXentry)


def test_group_class():

    group = NXgroup()
    group.nxclass = NXentry

    assert group.nxclass == "NXentry"
    assert isinstance(group, NXentry)


def test_group_components():

    g1 = NXdata(name="g1")
    g2 = NXdata(name="g2")
    g3 = NXdata(name="g3")
    group = NXentry(g1, g2, g3)

    assert group.component("NXdata") == [group["g1"], group["g2"], group["g3"]]
    assert group.NXdata == [group["g1"], group["g2"], group["g3"]]


def test_group_title():

    group = NXentry()
    group["title"] = "Group Title"

    assert group.nxtitle == "Group Title"


def test_group_move(field1):

    group = NXentry()
    group["g1"] = NXgroup()
    group["g1/f1"] = field1
    group["g2"] = NXgroup()
    group["g1"].move("f1", "g2", name="f2")

    assert "g1/f1" not in group
    assert "g2/f2" in group

    group["g2"].move(group["g2/f2"], group["g1"], name="f1")

    assert "g2/f2" not in group
    assert "g1/f1" in group

    group["g3"] = NXgroup()
    group["g2/f2"] = NXlink(target="g1/f1")
    group["g2"].move("f2", "g3", name="f3")

    assert group["g3/f3"].nxlink == field1


def test_group_copy(tmpdir, field1):

    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry())
    root.save(filename, mode="w")

    external_filename = os.path.join(tmpdir, "file2.nxs")
    external_root = NXroot(
        NXentry(NXgroup(field1, name="g1", attrs={"a": "b"})))
    external_root.save(external_filename, mode="w")

    root["entry/g2"] = NXlink(target="entry/g1", file=external_filename)

    copied_filename = os.path.join(tmpdir, "file3.nxs")
    copied_root = NXroot()
    copied_root.save(copied_filename, mode="w")

    copied_root["entry"] = root["entry"].copy(expand_external=True)

    assert "entry" in copied_root
    assert "g2" in copied_root["entry"]
    assert "entry/g2/f1" in copied_root
    assert not isinstance(copied_root["entry/g2"], NXlink)
    assert copied_root["entry/g2/f1"][0] == 1
    assert "a" in copied_root["entry/g2"].attrs
    assert copied_root["entry/g2"].attrs["a"] == "b"


def test_field_copy(tmpdir, field1):

    filename = os.path.join(tmpdir, "file1.nxs")
    root = NXroot(NXentry(NXgroup(name="g1")))
    root.save(filename, mode="w")

    external_filename = os.path.join(tmpdir, "file2.nxs")
    external_root = NXroot(NXentry(NXgroup(field1, name="g2")))
    external_root.save(external_filename, mode="w")

    root["entry/g1/f1"] = NXlink(target="entry/g2/f1", file=external_filename)

    copied_filename = os.path.join(tmpdir, "file3.nxs")
    copied_root = NXroot(NXentry(NXgroup(name="g3")))
    copied_root.save(copied_filename, mode="w")

    copied_root["entry/g3/f1"] = root["entry/g1/f1"].copy()

    assert "entry/g3/f1" in copied_root
    assert not isinstance(copied_root["entry/g3/f1"], NXlink)
    assert copied_root["entry/g3/f1"][0] == 1
