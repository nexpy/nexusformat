import numpy as np
import pytest
from nexusformat.nexus import *

x = NXfield(2 * np.linspace(0.0, 10.0, 11, dtype=np.float64), name="x")
y = NXfield(3 * np.linspace(0.0, 5.0, 6, dtype=np.float64), name="y")
z = NXfield(4 * np.linspace(0.0, 2.0, 3, dtype=np.float64), name="z")
v = NXfield(np.linspace(0, 10*5*2, num=10*5*2, dtype=np.float64), name="v")
v.resize((2,5,10))


def test_entry_operations():

    e1 = NXentry(NXdata(2*v, (z, y, x), name='d1'), NXsample(name='s1'))
    e1.attrs['default'] = 'd1'
    e2 = NXentry(NXdata(v, (z, y, x), name='d1'))
    
    e3 = e1 + e2

    assert 'd1' in e3
    assert 's1' in e3
    assert e3.attrs['default'] == 'd1'
    assert np.array_equal(e3.d1.nxsignal.nxvalue, 3*v)
    assert e3.d1.nxaxes == e1.d1.nxaxes
    assert e3.d1.nxsignal.nxname == "v"
    assert [axis.nxname for axis in e3.d1.nxaxes] == ["z", "y", "x"]

    e3 = e1 - e2

    assert 'd1' in e3
    assert 's1' in e3
    assert np.array_equal(e3.d1.nxsignal.nxvalue, v)
    assert e3.d1.nxaxes == e1.d1.nxaxes
    assert e3.d1.nxsignal.nxname == "v"
    assert [axis.nxname for axis in e3.d1.nxaxes] == ["z", "y", "x"]


def test_plottable_data():

    entry = NXentry(NXdata(v, (z, y, x), name='d1'), NXsample(name='s1'))

    assert entry.is_plottable()
    assert entry.plottable_data is entry['d1']

