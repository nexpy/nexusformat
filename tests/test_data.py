import numpy as np
import pytest
import warnings
from nexusformat.nexus import *

x = NXfield(2 * np.linspace(0.0, 10.0, 11, dtype=np.float64), name="x")
y = NXfield(3 * np.linspace(0.0, 5.0, 6, dtype=np.float64), name="y")
z = NXfield(4 * np.linspace(0.0, 2.0, 3, dtype=np.float64), name="z")
v = NXfield(np.linspace(0, 99, num=100, dtype=np.float64), name="v")
v.resize((2, 5, 10))
im = NXfield(np.ones(shape=(10, 10, 4), dtype=np.float32), name='image')


def test_data_creation():

    data = NXdata(v, (z, y, x), title="Title")
    
    assert "signal" in data.attrs
    assert "axes" in data.attrs
    assert len(data.attrs["axes"]) == 3
    
    assert data.ndim == 3
    assert data.shape == (2, 5, 10)
    assert data.nxsignal.nxname == "v"
    assert data.nxsignal.ndim == 3
    assert data.nxsignal.shape == (2, 5, 10)
    assert data.nxsignal.any()
    assert not data.nxsignal.all()
    assert [axis.nxname for axis in data.nxaxes] == ["z", "y", "x"]
    assert [axis.ndim for axis in data.nxaxes] == [1, 1, 1]
    assert [axis.shape for axis in data.nxaxes] == [(3,), (6,), (11,)]

    assert data.nxtitle == "Title"


def test_default_data():

    data = NXdata(v, (z, y, x), title="Title")
    root = NXroot(NXentry(data))
    root["entry/data"].set_default()

    assert root.get_default() is root["entry/data"]
    assert root["entry"].get_default() is root["entry/data"]
    assert root["entry/data"].get_default() is root["entry/data"]
    assert root.plottable_data is root["entry/data"]

    root["entry/subentry"] = NXsubentry(data)
    root["entry/subentry/data"].set_default()

    assert root.get_default() is root["entry/data"]
    assert root["entry/subentry"].get_default() is root["entry/subentry/data"]
    assert root["entry/subentry"].plottable_data is root["entry/subentry/data"]

    root["entry/subentry/data"].set_default(over=True)

    assert root.get_default() is root["entry/subentry/data"]
    assert root["entry"].get_default() is root["entry/subentry/data"]
    assert root["entry/data"].get_default() is root["entry/data"]
    assert root.plottable_data is root["entry/subentry/data"]


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


def test_data_projections():

    d1 = NXdata(v[0], (y, x))

    assert d1.nxaxes == [d1['y'], d1['x']]

    p1 = d1.project((1, 0))
    p2 = d1.project((0, 1), limits=((3., 9.), (4., 16.)))

    assert p1.nxaxes == [p1['x'], p1['y']]
    assert np.array_equal(p1['x'].nxvalue, d1['x'])
    assert p2.nxaxes == [p2['y'], p2['x']]
    assert np.array_equal(p2['x'].nxvalue, d1['x'][4.:16.])
    assert np.array_equal(p2['x'].nxvalue, d1['x'][2:9])

    d2 = NXdata(v, (z, y, x))

    p3 = d2.project((0,1),((0.,8.),(3.,9.),(4.,16.)))

    assert p3.nxaxes == [p3['z'], p3['y']]
    assert np.array_equal(p3['y'].nxvalue, d2['y'][3.:9.])
    assert np.array_equal(p3['y'].nxvalue, d2['y'][1:4])
    assert p3['x'] == 10.
    assert p3['x'].attrs['minimum'] == 4.
    assert p3['x'].attrs['maximum'] == 16.
    assert p3['x'].attrs['summed_bins'] == 7
    assert p3['v'].sum() == d2.v[:,1:3,2:8].sum()
    
    p4 = d2.project((0,1),((0.,8.),(3.,9.),(4.,16.)), summed=False)

    assert p4['v'].sum() == d2.v[:,1:3,2:8].sum() / p4['x'].attrs['summed_bins']


def test_data_smoothing():

    warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
    data = NXdata(np.sin(x), (x))
    smooth_data = data.smooth(n=100, xmin=x.min(), xmax=x.max())

    assert smooth_data.nxsignal.shape == (100,)
    assert smooth_data.nxaxes[0].shape == (100,)
    assert smooth_data.nxsignal[0] == np.sin(x)[0]
    assert smooth_data.nxsignal[-1] == np.sin(x)[-1]


def test_image_data():

    root = NXroot(NXentry(NXdata(im)))
    root['entry'].attrs['default'] = 'data'
    root['entry/other_data'] = NXdata(v, (z, y, x), title="Title")

    assert root['entry/data/image'].is_image()
    assert root['entry/data'].is_image()
    assert root.plottable_data.is_image()
    assert root['entry'].plottable_data.is_image()
    assert not root['entry/other_data'].is_image()
