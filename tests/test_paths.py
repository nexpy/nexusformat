from nexusformat.nexus.tree import NXentry, NXgroup, NXroot


def test_attribute_paths(field1):

    root = NXroot(NXentry())
    root.entry.g1 = NXgroup(field1)

    assert root.entry.g1.nxpath == "/entry/g1"
    assert root["entry/g1"] is root.entry.g1
    assert root["entry/g1/f1"] is root.entry.g1.f1
    assert "g1" in root.entry
    assert "f1" in root.entry.g1
    assert "entry/g1/f1" in root
    assert root.entry.g1.f1.nxroot is root


def test_dictionary_paths(field1):

    root = NXroot(NXentry())
    root["entry/g1"] = NXgroup(field1)

    assert root.entry.g1.nxpath == "/entry/g1"
    assert root["entry/g1"] is root.entry.g1
    assert root["entry/g1/f1"] is root.entry.g1.f1
    assert "g1" in root["/entry"]
    assert "f1" in root["/entry/g1"]
    assert "/entry/g1/f1" in root
    assert root["/entry/g1/f1"].nxroot is root


def test_relative_paths(field1):

    root = NXroot(NXentry())
    root["entry/g1"] = NXgroup()
    root["entry/g1/g2"] = NXgroup()
    root["entry/g1/g2/f1"] = field1

    assert "f1" in root["entry/g1/g2"]
    assert "g2/f1" in root["entry/g1"]
    assert "g1/g2/f1" in root["entry"]
    assert root["entry/g1/g2/f1"].nxpath == "/entry/g1/g2/f1"
    assert "entry" in root
