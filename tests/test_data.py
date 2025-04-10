import os
import warnings

import numpy as np
import pytest
from nexusformat.nexus.tree import (NXdata, NXentry, NXfield, NXroot,
                                    NXsubentry, NXvirtualfield, nxconsolidate,
                                    nxload)


@pytest.fixture
def data(x, y, z, v):
    """
    Returns a simple NXdata object with a title.
    """
    return NXdata(v, (z, y, x), title="Title")


@pytest.fixture
def data2(v):
    """
    Returns a different, simple NXdata object with a title.
    """
    v2 = v[0]
    v2.resize((1, 5, 10))
    return NXdata(v2)


@pytest.fixture
def empty_data():
    """
    Returns a default NXdata instance.
    """
    return NXdata()


@pytest.fixture
def NXdata_from_empty_01(empty_data, x, y, z, v):
    empty_data.nxsignal = v
    empty_data.nxaxes = (z, y, x)
    return empty_data


@pytest.fixture
def NXdata_from_empty_02(empty_data, x, y, z, v):
    empty_data["v"] = v
    empty_data["x"] = x
    empty_data["y"] = y
    empty_data["z"] = z
    empty_data.nxsignal = "v"
    empty_data.nxaxes = ("z", "y", "x")
    return empty_data


def test_data_creation(data):

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


def test_default_data(data):

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


def test_plottable_data_01(data):

    assert data.is_plottable()
    assert data.plottable_data is data
    assert data.plot_rank == 3
    assert data.plot_rank == data.nxsignal.ndim
    assert data.plot_axes == data.nxaxes
    assert data.nxsignal.valid_axes(data.nxaxes)


def test_plottable_data_02(data2):

    assert data2.shape == (1, 5, 10)
    assert data2.plot_shape == (5, 10)
    assert data2.plot_rank == 2
    assert data2.plot_rank == data2.nxsignal.ndim - 1


@pytest.mark.parametrize(
    "data_fixture_name",
    ['NXdata_from_empty_01',
     'NXdata_from_empty_02']
)
def test_signal_selection(data_fixture_name, z, v, request):

    data = request.getfixturevalue(data_fixture_name)
    assert data.nxsignal.nxname == "v"
    assert [axis.nxname for axis in data.nxaxes] == ["z", "y", "x"]
    assert np.array_equal(data.nxsignal, v)
    assert np.array_equal(data.nxaxes[0], z)


def test_rename(NXdata_from_empty_01):

    data = NXdata_from_empty_01
    data["x"].rename("xx")
    data["y"].rename("yy")
    data["z"].rename("zz")
    data["v"].rename("vv")
    assert data.nxsignal.nxname == "vv"
    assert [axis.nxname for axis in data.nxaxes] == ["zz", "yy", "xx"]


def test_size_one_axis(x, z):

    y1 = np.array((1), dtype=np.float64)
    v1 = NXfield(np.linspace(0, 10*1*2, num=10*1*2, dtype=np.int64), name="v")
    v1.resize((2, 1, 10))

    data = NXdata(v1, (z, y1, x))

    assert data.is_plottable()
    assert data.plottable_data is data
    assert data.plot_rank == 2
    assert data.plot_rank == data.nxsignal.ndim - 1
    assert len(data.plot_axes) == 2
    assert data.plot_shape == (2, 10)
    assert data.nxsignal.valid_axes(data.plot_axes)


def test_data_operations(data, v):

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
    e1 = NXfield(np.sqrt(v1))

    data = NXdata(v1, (y1), errors=e1)

    assert data.nxerrors is not None
    assert data.nxerrors.nxname == "v_errors"
    assert np.array_equal(data.nxerrors, e1)

    data = NXdata(v1, (y1))
    data.nxerrors = e1

    new_data = 2 * data

    assert np.array_equal(new_data.nxerrors, 2 * e1)

    new_data = 2 * data - data

    assert np.array_equal(new_data.nxerrors, e1 * np.sqrt(5))

    new_data = data - data / 2

    assert np.array_equal(new_data.nxerrors, e1 * np.sqrt(1.25))


def test_data_weights():

    y1 = NXfield(np.linspace(1, 10, 10), name="y")
    v1 = NXfield(y1**2, name="v")
    w1 = NXfield(np.sqrt(v1))

    data = NXdata(v1, (y1), errors=y1, weights=w1)

    assert data.nxweights is not None
    assert data.nxweights.nxname == "v_weights"
    assert np.array_equal(data.nxweights, w1)

    weighted_data = data.weighted_data()

    assert np.array_equal(weighted_data.nxsignal, v1 / w1)
    assert np.array_equal(weighted_data.nxerrors, y1 / w1)
    assert weighted_data.nxaxes == data.nxaxes

    data = NXdata(v1, (y1))
    data.nxweights = w1

    new_data = 2 * data

    assert np.array_equal(new_data.nxweights, 2 * w1)

    new_data = 2 * data - data

    assert np.array_equal(new_data.nxweights, w1)

    new_data = data - data / 2

    assert np.array_equal(new_data.nxweights, w1/2)


def test_data_angles(data):

    data.nxangles = [120, 90, 90]

    assert data.nxangles == [120.0, 90.0, 90.0]


def test_data_slabs(data, x, y, v):

    slab = data[0, :, :]

    assert np.array_equal(slab.nxsignal, v[0])
    assert slab.plot_rank == 2
    assert slab.plot_shape == v[0].shape
    assert slab.nxaxes == [y, x]

    slab = data[0, 3.:12., 2.:18.]

    assert slab.plot_shape == (v.shape[1]-2, v.shape[2]-2)
    assert slab.plot_axes == [y[1:-1], x[1:-1]]

    slab = data[0, 3.5:11.5, 2.5:17.5]

    assert slab.shape == (v.shape[1]-2, v.shape[2]-2)
    assert slab.plot_shape == (v.shape[1]-2, v.shape[2]-2)
    assert slab.plot_axes == [y[1:-1], x[1:-1]]

    slab1 = data[0:0, 3.5:11.5, 2.5:17.5]
    slab2 = data[0:1, 3.5:11.5, 2.5:17.5]

    assert slab1.shape == slab.shape
    assert slab2.shape == slab.shape


def test_data_projections(x, y, z, v):

    d1 = NXdata(v[0], (y, x))

    assert d1.nxaxes == [d1["y"], d1["x"]]

    p1 = d1.project((1, 0))
    p2 = d1.project((0, 1), limits=((3., 9.), (4., 16.)))

    assert p1.nxaxes == [p1["x"], p1["y"]]
    assert np.array_equal(p1["x"].nxvalue, d1["x"])
    assert p2.nxaxes == [p2["y"], p2["x"]]
    assert np.array_equal(p2["x"].nxvalue, d1["x"][4.:16.])
    assert np.array_equal(p2["x"].nxvalue, d1["x"][2:9])

    d2 = NXdata(v, (z, y, x))

    p3 = d2.project((0, 1), ((0., 8.), (3., 9.), (4., 16.)))

    assert p3.nxaxes == [p3["z"], p3["y"]]
    assert np.array_equal(p3["y"].nxvalue, d2["y"][3.:9.])
    assert np.array_equal(p3["y"].nxvalue, d2["y"][1:4])
    assert p3["x"] == 10.
    assert p3["x"].attrs["minimum"] == 4.
    assert p3["x"].attrs["maximum"] == 16.
    assert p3["x"].attrs["summed_bins"] == 7
    assert p3["v"].sum() == d2.v[:, 1:3, 2:8].sum()

    p4 = d2.project((0, 1), ((0., 8.), (3., 9.), (4., 16.)), summed=False)

    assert p4["v"].sum() == d2.v[:, 1:3, 2:8].sum() / \
        p4["x"].attrs["summed_bins"]


def test_data_transpose(data):

    signal = data.nxsignal
    assert data.transpose().shape == signal.shape[::-1]
    axes = [2, 0, 1]
    transposed_data = data.transpose(axes)
    assert transposed_data.shape == signal.transpose(axes).shape
    assert ([axis.nxname for axis in transposed_data.nxaxes] ==
            [data.nxaxes[i].nxname for i in axes])


def test_data_smoothing(x):

    warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
    data = NXdata(np.sin(x), (x))
    smooth_data = data.smooth(n=101, xmin=x.min(), xmax=x.max())

    assert smooth_data.nxsignal.shape == (101,)
    assert smooth_data.nxaxes[0].shape == (101,)
    assert smooth_data.nxsignal[0] == pytest.approx(np.sin(x)[0])
    assert smooth_data.nxsignal[-1] == pytest.approx(np.sin(x)[-1])

    smooth_data = data.smooth(factor=4)

    assert smooth_data.nxsignal.shape == (41,)
    assert smooth_data.nxaxes[0].shape == (41,)
    assert smooth_data.nxsignal[0] == pytest.approx(np.sin(x)[0])
    assert smooth_data.nxsignal[4] == pytest.approx(np.sin(x)[1])
    assert smooth_data.nxsignal[-1] == pytest.approx(np.sin(x)[-1])


def test_data_selection():

    xx = np.linspace(0, 20.0, 21, dtype=float)
    yy = np.ones(shape=xx.shape, dtype=float)
    yy[np.where(np.remainder(xx, 4) == 0.0)] = 2.0
    data = NXdata(yy, xx)

    selected_data = data.select(4.0)

    assert selected_data.shape == (6,)
    assert np.all(selected_data.nxsignal == 2.0)

    yy[(np.array((1, 3, 5, 7, 9, 11, 13, 15, 17, 19)),)] = 1.5
    data = NXdata(yy, xx)

    selected_data = data.select(4.0, offset=1.0)

    assert selected_data.shape == (5,)
    assert np.all(selected_data.nxsignal == 1.5)

    selected_data = data.select(4.0, offset=1.0, symmetric=True)

    assert selected_data.shape == (10,)
    assert np.all(selected_data.nxsignal == 1.5)


def test_data_moments(peak1D, arr1D):

    data = NXdata(peak1D, arr1D)

    assert data.sum() == data.nxsignal.nxvalue.sum()
    assert np.isclose(data.moment(1), 50.0, rtol=1e-3)
    assert np.isclose(data.moment(2), 100.0, rtol=1e-3)
    assert np.isclose(data.std(), 10.0, rtol=1e-3)
    assert np.isclose(data.average(), data.nxsignal.nxvalue.sum() / 101.0)


def test_image_data(x, y, z, v, im):

    root = NXroot(NXentry(NXdata(im)))
    root["entry"].attrs["default"] = "data"
    root["entry/other_data"] = NXdata(v, (z, y, x), title="Title")

    assert root["entry/data/image"].is_image()
    assert root["entry/data"].is_image()
    assert root.plottable_data.is_image()
    assert root["entry"].plottable_data.is_image()
    assert not root["entry/other_data"].is_image()


def test_smart_indices(x, v):

    ind = [1, 3, 5]

    assert all(x[ind].nxvalue == x.nxvalue[ind])
    assert all(v[v > 50].nxvalue == v.nxvalue[v.nxvalue > 50])
    assert all(v[1, 0, ind].nxvalue == v.nxvalue[1, 0, ind])

    x[ind] = 0

    assert x.any() and not x[ind].any()

    ind = np.array([[3, 7], [4, 5]])

    assert np.all(x[ind].nxvalue == x.nxvalue[ind])

    row = np.array([0, 1, 2])
    col = np.array([2, 1, 3])

    assert all(v[0][row, col].nxvalue == v[0].nxvalue[row, col])
    assert np.all(v[0][row[:, np.newaxis], col].nxvalue ==
                  v[0].nxvalue[row[:, np.newaxis], col])


@pytest.mark.parametrize("path", [True, False])
def test_virtual_fields(tmpdir, path, v):

    s1 = NXroot(NXentry(NXdata(v)))
    s2 = NXroot(NXentry(NXdata(2*v)))
    s3 = NXroot(NXentry(NXdata(3*v)))

    s1.save(os.path.join(tmpdir, "s1.nxs"), "w")
    s2.save(os.path.join(tmpdir, "s2.nxs"), "w")
    s3.save(os.path.join(tmpdir, "s3.nxs"), "w")

    sources = [f.nxfilename for f in [s1, s2, s3]]

    if path:
        vds1 = NXvirtualfield("entry/data/v", sources, shape=v.shape,
                              dtype=v.dtype)
    else:
        vds1 = NXvirtualfield(s1["entry/data/v"], sources)

    assert vds1.shape == (3,) + v.shape
    assert vds1.dtype == v.dtype
    assert vds1.sum() == 6 * v.sum()

    vds2 = nxconsolidate(sources, "entry/data")

    assert vds2.nxsignal.shape == vds1.shape
    assert vds2.nxsignal.dtype == v.dtype
    assert vds2.sum() == 6 * v.sum()

    NXroot(NXentry(vds2)).save(os.path.join(tmpdir, "vds.nxs"), "w")
    vds3 = nxload(os.path.join(tmpdir, "vds.nxs"))

    assert "entry/data/v" in vds3
    assert vds3["entry/data/v"].shape == vds1.shape
    assert vds3["entry/data/v"].dtype == v.dtype
    assert vds3["entry/data/v"].sum() == 6 * v.sum()
    assert vds3.nxfile["entry/data/v"].is_virtual


def test_data_signals(arr1D):

    x = NXfield(arr1D, dtype=np.float64, name="x")
    y = NXfield(2 * arr1D, dtype=np.float64, name="y")
    y1 = NXfield(3 * arr1D, dtype=np.float64, name="y1")
    y2 = NXfield(4 * arr1D, dtype=np.float64, name="y2")
    data = NXdata(y, [x], y1=y1, y2=y2)
    data.nxauxiliary_signals = ["y1", "y2"]

    assert data.nxauxiliary_signals == [data["y1"], data["y2"]]
    assert data.nxsignals == [data["y"], data["y1"], data["y2"]]

    data = NXdata(y, [x], y1=y1, y2=y2)
    data.nxauxiliary_signals = [data["y1"], data["y2"]]

    assert data.nxauxiliary_signals == [data["y1"], data["y2"]]
    assert data.nxsignals == [data["y"], data["y1"], data["y2"]]


def test_data_indices(arr2D):

    v = NXfield(arr2D, dtype=np.float64, name="v")
    x = NXfield(arr2D[1], dtype=np.float64, name="x")
    y = NXfield(arr2D[0], dtype=np.float64, name="y")
    z = NXfield(arr2D, dtype=np.float64, name="z")
    data = NXdata(v, (y, x), z=z)
    data.nxindices = {"x": 0, "z": [0, 1]}

    assert data.nxindices == {"x": 0, "z": [0, 1]}


def test_data_coordinates(arr1D):

    x = NXfield(arr1D, dtype=np.float64, name="x")
    y = NXfield(arr1D, dtype=np.float64, name="y")
    z = NXfield(arr1D, dtype=np.float64, name="z")
    data = NXdata(z, x=x, y=y)
    data.nxcoordinates = ["y", "x"]

    assert data.nxcoordinates == [data["y"], data["x"]]

    data = NXdata(z, x=x, y=y)
    data.nxcoordinates = [data["y"], data["x"]]

    assert data.nxcoordinates == [data["y"], data["x"]]
