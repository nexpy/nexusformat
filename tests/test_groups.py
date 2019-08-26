import h5py as h5
import numpy as np
import pytest
import six
from nexusformat.nexus import *


field1 = NXfield((1,2), name="f1")
field2 = NXfield((3,4), name="f2")
field3 = NXfield((5,6), name="f3")


def test_group_creation():

    group1 = NXgroup()

    assert len(group1) == 0
    
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

    group3 = NXgroup(g1=group1)

    assert "g1/g2/f1" in group3
    

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


def test_group_title():

    group = NXentry()
    group["title"] = "Group Title"

    assert group.nxtitle == "Group Title"
