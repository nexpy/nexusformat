import numpy as np
import pytest
from nexusformat.nexus import *

x = NXfield(2 * np.linspace(0.0, 10.0, 11, dtype=np.float64), name="x")
y = NXfield(3 * np.linspace(0.0, 5.0, 6, dtype=np.float64), name="y")
z = NXfield(4 * np.linspace(0.0, 2.0, 3, dtype=np.float64), name="z")
v = NXfield(np.linspace(0, 10*5*2, num=10*5*2, dtype=np.float64), name="v")
v.resize((2,5,10))


def test_data_creation():

    data = NXdata(v, (z, y, x), title="Title")
    
    assert "signal" in data.attrs
    assert "axes" in data.attrs
    assert len(data.attrs["axes"]) == 3
    
    assert data.nxsignal.nxname == "v"
    assert data.nxsignal.ndim == 3
    assert data.nxsignal.shape == (2, 5, 10)
    assert [axis.nxname for axis in data.nxaxes] == ["z", "y", "x"]
    assert [axis.ndim for axis in data.nxaxes] == [1, 1, 1]
    assert [axis.shape for axis in data.nxaxes] == [(3,), (6,), (11,)]

    assert data.nxtitle == "Title"


def test_plottable_data():

    data = NXdata(v, (z, y, x), title="Title")

    assert data.is_plottable()
    assert data.plottable_data is data
    assert data.plot_rank == 3
    assert data.plot_rank == data.nxsignal.ndim
    assert data.plot_axes == data.nxaxes
    assert data.nxsignal.valid_axes(data.nxaxes)


def test_signal_selection():

    data = NXdata()
    data.nxsignal = v
    data.nxaxes = (z, y, x)

    assert data.nxsignal.nxname == "v"
    assert [axis.nxname for axis in data.nxaxes] == ["z", "y", "x"]


def test_size_one_axis():

    y1 = np.array((1), dtype=np.float64)
    v1 =  NXfield(np.linspace(0, 10*1*2, num=10*1*2, dtype=np.int64), name="v")
    v1.resize((2,1,10))

    data = NXdata(v1, (z, y1, x))

    assert data.is_plottable()
    assert data.plottable_data is data
    assert data.plot_rank == 2
    assert data.plot_rank == data.nxsignal.ndim - 1
    assert len(data.plot_axes) == 2
    assert data.plot_shape == (2, 10)
    assert data.nxsignal.valid_axes(data.plot_axes)


def test_data_operations():

    data = NXdata(v, (z, y, x))
    new_data = data + 1

    assert np.array_equal(new_data.nxsignal.nxvalue, v + 1)
    assert new_data.nxaxes == data.nxaxes
    assert new_data.nxsignal.nxname == "v"
    assert [axis.nxname for axis in data.nxaxes] == ["z", "y", "x"]

    new_data = data - 1

    assert np.array_equal(new_data.nxsignal, v - 1)

    new_data = data * 2

    assert np.array_equal(new_data.nxsignal, v * 2)

    new_data = 2 * data

    assert np.array_equal(new_data.nxsignal, v * 2)

    new_data = data / 2

    assert np.array_equal(new_data.nxsignal, v / 2)

    new_data = 2 * data - data

    assert np.array_equal(new_data.nxsignal, v)


def test_data_errors():

    y1 = NXfield(np.linspace(1, 10, 10), name="y")
    v1 = NXfield(y1**2, name="v")
    e1 = NXfield(np.sqrt(v1), name="e")

    data = NXdata(v1, (y1), errors=e1)

    assert data.nxerrors.nxname == "e"
    assert np.array_equal(data.nxerrors, e1)

    new_data = 2 * data

    assert np.array_equal(new_data.nxerrors, 2 * e1)

    new_data = 2 * data - data

    assert np.array_equal(new_data.nxerrors, e1 * np.sqrt(5))
 
    new_data = data - data / 2

    assert np.array_equal(new_data.nxerrors, e1 * np.sqrt(1.25))
   

def test_data_slabs():

    data = NXdata(v, (z, y, x), title="Title")
 
    slab = data[0,:,:]

    assert np.array_equal(slab.nxsignal, v[0])
    assert slab.plot_rank == 2
    assert slab.plot_shape == v[0].shape
    assert slab.nxaxes == [y, x]

    slab = data[0, 3.:12., 2.:18.]

    assert slab.plot_shape == (v.shape[1]-2, v.shape[2]-2)
    assert slab.plot_axes == [y[1:-1], x[1:-1]]

    slab = data[0, 3.5:11.5, 2.5:17.5]

    assert slab.plot_shape == (v.shape[1]-2, v.shape[2]-2)
    assert slab.plot_axes == [y[1:-1], x[1:-1]]
