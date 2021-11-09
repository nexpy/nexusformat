"""
Pytest automatically parses this module for fixtures that can be used in its
directory, as well as in any of its subdirectories.

This module contains fixtures that return generic NXfields.
"""

from pytest import fixture
import numpy as np

from nexusformat.nexus.tree import NXfield, NXdata


@fixture
def x():
    return NXfield(2 * np.linspace(0.0, 10.0, 11, dtype=np.float64), name="x")


@fixture
def y():
    return NXfield(3 * np.linspace(0.0, 5.0, 6, dtype=np.float64), name="y")


@fixture
def z():
    return NXfield(4 * np.linspace(0.0, 2.0, 3, dtype=np.float64), name="z")


@fixture
def v():
    v = NXfield(np.linspace(0, 99, num=100, dtype=np.float64), name="v")
    v.resize((2, 5, 10))
    return v


@fixture
def im():
    return NXfield(np.ones(shape=(10, 10, 4), dtype=np.float32), name='image')
