import pytest
from nexusformat.nexus import *


field1 = NXfield((1,2), name="f1")
field2 = NXfield((3,4), name="f2")
field3 = NXfield((5,6), name="f3")


def test_group_creation():

    group1 = NXgroup(name="group")

    assert len(group1) == 0
    assert group1.nxname == "group"
    assert group1.nxgroup is None

    group2 = NXgroup(field1)

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


def test_group_insertion():

    group1 = NXgroup()

    group1.insert(field2, name="f1")

    assert "f1" in group1
    assert len(group1) == 1


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


def test_group_title():

    group = NXentry()
    group["title"] = "Group Title"

    assert group.nxtitle == "Group Title"


def test_group_move():

    group = NXentry()
    group['g1'] = NXgroup()
    group['g1/f1'] = field1
    group['g2'] = NXgroup()
    group['g1'].move('f1', 'g2', name='f2')

    assert 'g1/f1' not in group
    assert 'g2/f2' in group

    group['g2'].move(group['g2/f2'], group['g1'], name='f1')

    assert 'g2/f2' not in group
    assert 'g1/f1' in group

    group['g3'] = NXgroup()
    group['g2/f2'] = NXlink(target='g1/f1')
    group['g2'].move('f2', 'g3', name='f3')

    assert group['g3/f3'].nxlink == field1

    
def test_group_copy():

    group = NXentry()
    group['g1'] = NXgroup()
    group['g1/g2'] = NXgroup()
    group['g1/g2/f1'] = field1

    new_group = group['g1/g2'].copy()
    assert new_group.entries == group['g1/g2'].entries
    assert id(new_group['f1']) != id(group['g1/g2/f1'])

    group['g3'] = NXgroup()
    group['g1/g2'].copy(group['g3'], name='g4')

    assert 'g3/g4/f1' in group
    assert group['g1/g2/f1'] == group['g3/g4/f1']

