import numpy as np
import pytest
from nexusformat.nexus.tree import NXdata, NXentry, NXsample


@pytest.fixture
def entry_1(x, y, z, v):
    """Simple entry."""
    entry = NXentry(NXdata(2*v, (z, y, x), name='d1'), NXsample(name='s1'))
    entry.attrs['default'] = 'd1'
    return entry


@pytest.fixture
def entry_2(x, y, z, v):
    """Simple entry, but different to entry_1"""
    return NXentry(NXdata(v, (z, y, x), name='d1'))


@pytest.fixture
def entry_3(entry_1, entry_2):
    """Simple linear combination of entries."""
    return entry_1 + entry_2


@pytest.fixture
def entry_4(entry_1, entry_2):
    """Second simple linear combination of entries"""
    return entry_1 - entry_2


def test_entry_operation_values(entry_3, entry_4, v):

    assert np.array_equal(entry_3.d1.nxsignal.nxvalue, 3*v)
    assert np.array_equal(entry_4.d1.nxsignal.nxvalue, v)


@pytest.mark.parametrize(
    "entry",
    ['entry_3', 'entry_4']
)
def test_entry_operations(entry, entry_1, request):

    entry = request.getfixturevalue(entry)
    assert 'd1' in entry
    assert 's1' in entry
    assert entry.attrs['default'] == 'd1'

    assert entry.d1.nxaxes == entry_1.d1.nxaxes
    assert entry.d1.nxsignal.nxname == "v"
    assert [axis.nxname for axis in entry.d1.nxaxes] == ["z", "y", "x"]


def test_plottable_data(entry_2):

    assert entry_2.is_plottable()
    assert entry_2.plottable_data is entry_2['d1']
