import os

import numpy as np
import pytest
from nexusformat.nexus.tree import NXfield, NXgroup, NXroot, nxload


def test_field_masks(arr1D):
    field = NXfield(arr1D)
    field[10:20] = np.ma.masked

    assert isinstance(field.nxvalue, np.ma.masked_array)
    assert np.all(field[8:12].mask == np.array([False, False, True, True]))
    assert np.all(field.mask[8:12] == np.array([False, False, True, True]))
    assert np.ma.is_masked(field[8:12].nxvalue)
    assert np.ma.is_masked(field.nxvalue[10])
    assert np.ma.is_masked(field[10].nxvalue)
    assert field[10].mask

    field.mask[10] = np.ma.nomask

    assert np.all(field.mask[8:12] == np.array([False, False, False, True]))
    assert not field[10].mask


@pytest.mark.parametrize("save", ["False", "True"])
def test_group_masks(tmpdir, arr1D, save):
    group = NXgroup(NXfield(arr1D, name='field'))
    group['field'][10:20] = np.ma.masked

    if save:
        root = NXroot(group)
        filename = os.path.join(tmpdir, "file1.nxs")
        root.save(filename, mode="w")
        root = nxload(filename, "rw")
        group = root['group']

    assert isinstance(group['field'].nxvalue, np.ma.masked_array)
    assert np.all(group['field'].mask[9:11] == np.array([False, True]))
    assert 'mask' in group['field'].attrs
    assert group['field'].attrs['mask'] == 'field_mask'
    assert 'field_mask' in group
    assert group['field_mask'].dtype == bool
    assert group['field'].mask == group['field_mask']

    group['field'].mask[10] = np.ma.nomask

    assert np.all(group['field'].mask[10:12] == np.array([False, True]))
    assert np.all(group['field_mask'][10:12] == np.array([False, True]))
