"""
Pytest automatically parses this module for fixtures that can be used in its
directory, as well as in any of its subdirectories.

This module contains fixtures that return generic NXfields.
"""

from pytest import fixture
import numpy as np

from nexusformat.nexus.tree import NXfield


@fixture
def x():
    return NXfield(2 * np.linspace(0.0, 10, 11, dtype=np.float64), name="x")


@fixture
def y():
    return NXfield(3 * np.linspace(0.0, 5.0, 6, dtype=np.float64), name="y")


@fixture
def z():
    return NXfield(4 * np.linspace(0.0, 2.0, 3, dtype=np.float64), name="z")


@fixture
def field1():
    return NXfield((1, 2), name="f1")


@fixture
def field2():
    return NXfield((3, 4), name="f2")


@fixture
def field3():
    return NXfield((5, 6), name="f3")


@fixture
def field4():
    return NXfield("a", name="f1")


@fixture
def arr1D():
    return np.linspace(0.0, 100.0, 101, dtype=np.float64)


@fixture
def arr2D():
    return np.array(((1, 2, 3, 4), (5, 6, 7, 8)), dtype=np.int32)


@fixture
def arr3D():
    return np.resize(np.linspace(0.0, 124.0, 125, dtype=np.float64), (5, 5, 5))


@fixture
def v():
    v = NXfield(np.linspace(0, 99, num=100, dtype=np.float64), name="v")
    v.resize((2, 5, 10))
    return v


@fixture
def im():
    return NXfield(np.ones(shape=(10, 10, 4), dtype=np.float32), name="image")


@fixture
def peak1D():
    x = np.linspace(0.0, 100.0, 101, dtype=np.float64)
    return NXfield(np.exp(-(x - 50)**2 / 200), name="peak")
