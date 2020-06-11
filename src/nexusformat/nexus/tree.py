#!/usr/bin/env python 
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
# Copyright (c) 2013-2019, NeXpy Development Team.
#
# Author: Paul Kienzle, Ray Osborn
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
#-----------------------------------------------------------------------------

"""Module to read, write, analyze, manipulate, and visualize NeXus data.

This is designed to accomplish two goals:

    1. To provide convenient access to existing data contained in NeXus files.
    2. To enable new NeXus data to be created and manipulated interactively.

These goals are achieved by mapping hierarchical NeXus data structures directly
into Python objects, which represent NeXus groups, fields, or attributes.
Entries in a group are referenced as a dictionary containing other groups or 
fields. The entire data hierarchy can be referenced at any time, whether the
NeXus data has been loaded from an existing NeXus file or created dynamically
within the Python session. This provides a natural scripting interface for the 
creation, manipulation, and visualization of NeXus data.

Example 1: Loading a NeXus file
-------------------------------
The following commands loads NeXus data from a file, displays the contents as a 
tree, and then accesses individual data items. Note that all the classes and 
functions returned by the wildcard import in the example start with 'NX' or 
'nx' so name clashes with other modules are unlikely. 

    >>> from nexusformat.nexus import *
    >>> a=nxload('sns/data/ARCS_7326.nxs')
    >>> print a.tree
    root:NXroot
      @HDF5_Version = 1.8.2
      @NeXus_version = 4.2.1
      @file_name = ARCS_7326.nxs
      @file_time = 2010-05-05T01:59:25-05:00
      entry:NXentry
        data:NXdata
          data = float32(631x461x4x825)
            @axes = rotation_angle:tilt_angle:sample_angle:time_of_flight
            @signal = 1
          rotation_angle = float32(632)
            @units = degree
          sample_angle = [ 210.  215.  220.  225.  230.]
            @units = degree
          tilt_angle = float32(462)
            @units = degree
          time_of_flight = float32(826)
            @units = microsecond
        run_number = 7326
        sample:NXsample
          pulse_time = 2854.94747365
            @units = microsecond
    .
    .
    .
    >>> a['entry/run_number']
    NXfield(7326)

The tree returned from :func:`nxload()` has an entry for each group, field and
attribute.  You can traverse the hierarchy using the names of the groups.  For
example, tree['entry/instrument/detector/distance'] is an example of a field
containing the distance to each pixel in the detector. Entries can also be
referenced by NXclass name, such as ``tree.NXentry[0].instrument``. Since there 
may be multiple entries of the same NeXus class, the ``NXclass`` attribute 
returns a (possibly empty) list.

The :func:`nxload()` and :func:`nxsave()` functions are implemented using the 
:class:`NXFile` class, a subclass of :class:`h5py.File`.

Example 2: Creating a NeXus file dynamically
--------------------------------------------
The second example shows how to create NeXus data dynamically and saves it to a
file. The data are first created as Numpy arrays

    >>> import numpy as np
    >>> x=y=np.linspace(0,2*np.pi,101)
    >>> X,Y=np.meshgrid(y,x)
    >>> z=np.sin(X)*np.sin(Y)

Then, a NeXus data group is created and the data inserted to produce a
NeXus-compliant structure that can be saved to a file

    >>> root=NXroot(NXentry())
    >>> print root.tree
    root:NXroot
      entry:NXentry
    >>> root.entry.data=NXdata(z,[x,y])

Note that in this example, we have used the alternative attribute form
for accessing objects in the hierarchical structure, *i.e.*, 
`root.entry.data` instead of `root['entry/data']`. The attribute form is
faster to type interactively, but the dictionary form is safer for scripts
when there is a chance of clashes with class attributes or methods.

Additional metadata can be inserted before saving the data to a file.

    >>> root.entry.sample=NXsample()
    >>> root.entry.sample.temperature = 40.0
    >>> root.entry.sample.temperature.units = 'K'
    >>> root.save('example.nxs')

:class:`NXfield` objects have much of the functionality of Numpy arrays. They 
may be used in simple arithmetic expressions with other NXfields, Numpy 
arrays or scalar values and will be cast as ndarray objects if used as 
arguments in Numpy modules.

    >>> x=nx.NXfield(np.linspace(0,10.0,11))
    >>> x
    NXfield([  0.   1.   2. ...,   8.   9.  10.])
    >>> x + 10
    NXfield([ 10.  11.  12. ...,  18.  19.  20.])
    >>> np.sin(x)
    array([ 0.        ,  0.84147098,  0.90929743, ...,  0.98935825,
        0.41211849, -0.54402111])

If the arithmetic operation is assigned to a NeXus group attribute, it will be
automatically cast as a valid :class:`NXfield` object with the type and shape 
determined by the Numpy array type and shape.

    >>> entry.data.result = np.sin(x)
    >>> entry.data.result
    NXfield([ 0.          0.84147098  0.90929743 ...,  0.98935825  0.41211849
     -0.54402111])
    >>> entry.data.result.dtype, entry.data.result.shape
    (dtype('float64'), (11,))

Notes
-----
Properties of the entry in the tree are referenced by attributes that depend
on the object type, different nx attributes may be available.

Objects (:class:`NXobject`) have attributes shared by both groups and fields::
    * nxname   object name
    * nxclass  object class for groups, 'NXfield' for fields
    * nxgroup  group containing the entry, or None for the root
    * attrs    dictionary of NeXus attributes for the object

Fields (:class:`NXfield`) have attributes for accessing data:
    * shape    dimensions of data in the field
    * dtype    data type
    * nxdata   data in the field

Groups (:class:`NXgroup`) have attributes for accessing children::
    * entries  dictionary of entries within the group
    * component('nxclass')  return group entries of a particular class
    * dir()    print the list of entries in the group
    * tree     return the list of entries and subentries in the group
    * plot()   plot signal and axes for the group, if available

Linked fields or groups (:class:`NXlink`) have attributes for accessing the 
link::
    * nxlink   reference to the linked field or group

NeXus attributes (:class:`NXattr`) have a type and a value only::
    * dtype    attribute type
    * nxdata   attribute data

There is a subclass of :class:`NXgroup` for each group class defined by the 
NeXus standard, so it is possible to create an :class:`NXgroup` of NeXus 
:class:`NXsample` directly using:

    >>> sample = NXsample()

The default group name will be the class name following the 'NX', so the above
group will have an nxname of 'sample'. However, this is overridden by the
attribute name when it is assigned as a group attribute, e.g.,

    >>> entry.sample1 = NXsample()
    >>> entry.sample1.nxname
    sample1

You can traverse the tree by component class instead of component name. Since
there may be multiple components of the same class in one group you will need to
specify which one to use.  For example::

    tree.NXentry[0].NXinstrument[0].NXdetector[0].distance

references the first detector of the first instrument of the first entry.
Unfortunately, there is no guarantee regarding the order of the entries, and it
may vary from call to call, so this is mainly useful in iterative searches.
"""
from __future__ import absolute_import, division, print_function

import numbers
import os
import re
import sys
import warnings
from copy import copy, deepcopy

import h5py as h5
import numpy as np
import six

from .. import __version__ as nxversion
from .lock import NXLock, NXLockException

warnings.simplefilter(action='ignore', category=FutureWarning)

NX_MEMORY = 2000 #Memory in MB
NX_COMPRESSION = 'gzip'
NX_ENCODING = sys.getfilesystemencoding()
NX_MAXSIZE = 10000
NX_LOCK = 0

np.set_printoptions(threshold=5, precision=6)
string_dtype = h5.special_dtype(vlen=six.text_type)

__all__ = ['NXFile', 'NXobject', 'NXfield', 'NXgroup', 'NXattr', 
           'NXlink', 'NXlinkfield', 'NXlinkgroup', 'NeXusError', 
           'nxgetlock', 'nxsetlock', 'nxgetmemory', 'nxsetmemory', 
           'nxgetcompression', 'nxsetcompression', 
           'nxgetencoding', 'nxsetencoding', 'nxgetmaxsize', 'nxsetmaxsize',
           'nxclasses', 'nxload', 'nxsave', 'nxduplicate', 'nxdir', 'nxdemo',
           'nxversion']

#List of defined base classes (later added to __all__)
nxclasses = ['NXroot', 'NXentry', 'NXsubentry', 'NXdata', 'NXmonitor', 'NXlog', 
             'NXsample', 'NXinstrument', 'NXaperture', 'NXattenuator', 'NXbeam', 
             'NXbeam_stop', 'NXbending_magnet', 'NXcapillary', 'NXcite',
             'NXcollection', 'NXcollimator', 'NXcrystal', 'NXdetector', 
             'NXdetector_group', 'NXdetector_module', 'NXdisk_chopper', 
             'NXenvironment', 'NXevent_data', 'NXfermi_chopper', 'NXfilter', 
             'NXflipper', 'NXgeometry', 'NXgrating', 'NXgoniometer', 'NXguide', 
             'NXinsertion_device', 'NXmirror', 'NXmoderator', 'NXmonochromator', 
             'NXnote', 'NXorientation', 'NXparameters', 'NXpinhole', 
             'NXpolarizer', 'NXpositioner', 'NXprocess', 'NXreflections', 
             'NXsample_component', 'NXsensor', 'NXshape', 'NXslit', 'NXsource', 
             'NXtransformations', 'NXtranslation', 'NXuser', 
             'NXvelocity_selector', 'NXxraylens']

if six.PY2:
    FileNotFoundError = IOError
else:
    unicode = str


def text(value):
    """Return a unicode string in both Python 2 and 3.
    
    Parameters
    ----------
    value : str or bytes
        String or byte array to be converted.
    
    Returns
    -------
    str
        Converted unicode string
    
    Notes
    -----
    If the argument is a byte array, the function will decode the array using
    the encoding specified by NX_ENCODING, which is initially set to the
    system's default encoding, usually 'utf-8'. If this generates a 
    UnicodeDecodeError exception, an alternate encoding is tried. Null 
    characters are removed from the return value.
    """
    if isinstance(value, np.ndarray) and value.shape == (1,):
        value = value[0]
    if isinstance(value, bytes):
        try:
            _text = value.decode(NX_ENCODING)
        except UnicodeDecodeError:
            if NX_ENCODING == 'utf-8':
                _text = value.decode('latin-1')
            else:
                _text = value.decode('utf-8')
    elif isinstance(value, float):
        _text = format_float(value)
    elif six.PY3:
        _text = str(value)
    else:
        _text = unicode(value)
    return _text.replace('\x00','').rstrip()


def is_text(value):
    """Return True if the value represents text in both Python 2 and 3.
    
    Parameters
    ----------
    value : str or bytes
        Value to be checked.
    
    Returns
    -------
    bool
        True if the value is a string or bytes array.
    """
    if isinstance(value, bytes) or isinstance(value, six.string_types):
        return True
    else:
        return False


def is_string_dtype(dtype):
    """Return True if the dtype corresponds to a string type.
    
    Parameters
    ----------
    dtype : np.dtype
        Numpy data type to be tested.
    
    Returns
    -------
    bool
        True if the dtype corresponds to a string type.
    """
    return dtype == string_dtype or dtype.kind == 'S' or dtype.kind == 'U'


def is_iterable(obj):
    """Return True if the object is a list or a tuple.
    
    Parameters
    ----------
    obj : list or tuple
        Object to be tested.
    
    Returns
    -------
    bool
        True if the object is a list or a tuple.
    """
    return isinstance(obj, list) or isinstance(obj, tuple)


def format_float(value, width=np.get_printoptions()['precision']):
    """Return a float value with the specified width.
    
    This function results in a more compact scientific notation where relevant.
    """
    text = "{:.{width}g}".format(value, width=width)
    return re.sub(r"e(-?)0*(\d+)", r"e\1\2", text.replace("e+", "e"))


def natural_sort(key):
    """Key to sort a list of strings containing numbers in natural order.

    This function is used to customize the sorting of lists of strings. For 
    example, it ensures that 'label_10' follows 'label_9' after sorting.
    
    Parameters
    ----------
    key : str
        String in the list to be sorted.
    
    Returns
    -------
    list
        List of string components splitting embedded numbers as integers.
    """
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', key)]    


class NeXusError(Exception):
    """NeXus Error"""
    pass


class NXFile(object):
    """Interface for input/output to NeXus files using h5py.

    Usage::

      file = NXFile(filename, ['r','rw','w'])
        - open the NeXus file
      root = file.readfile()
        - read the structure of the NeXus file.  This returns a NeXus tree.
      file.writefile(root)
        - write a NeXus tree to the file.

    Example
    -------

      nx = NXFile('REF_L_1346.nxs','r')
      root = nx.readfile()
      for entry in root.NXentry:
          process(entry)
      copy = NXFile('modified.nxs','w')
      copy.writefile(root)

    Note that the large datasets are not loaded immediately.  Instead, the
    when the data set is requested, the file is reopened, the data read, and
    the file closed again. 
    """

    def __init__(self, name, mode='r', **kwargs):
        """Open an HDF5 file for reading and writing NeXus files.

        This creates a h5py File instance that is used for all subsequent
        input and output. Unlike h5py, where a closed file is no longer 
        accessible, the NXFile instance is persistent, and can be used to
        with a context manager to ensure that all file operations are 
        completed and the h5py File is released. A file locking mechanism
        is optionally available to prevent corruption of the file when 
        being accessed by multiple processes.
        
        Parameters
        ----------
        name : str
            Name of the HDF5 file.
        mode : {'r', 'rw', 'r+', 'w', 'w-', 'a'}
            Read/write mode of the HDF5 file, by default 'r'. These all have 
            the same meaning as their h5py counterparts, apart from 'rw', 
            which is equivelent to 'r+'. After creating and/or opening the 
            file, the mode is set to 'r' or 'rw' for remaining operations.
        **kwargs
            Keyword arguments to be used when opening the h5py File object.
        """
        self.h5 = h5
        self.name = name
        self._file = None
        self._filename = os.path.abspath(name)
        self._lock = NXLock(self._filename, timeout=NX_LOCK)
        self._path = '/'
        self._root = None
        self._with_count = 0
        if mode == 'w4' or mode == 'wx':
            raise NeXusError("Only HDF5 files supported")
        elif not os.path.exists(os.path.dirname(self._filename)):
            raise NeXusError("'%s/' does not exist"
                             % os.path.dirname(self._filename))
        elif (mode == 'w' or mode == 'w-' or mode == 'w5' or mode == 'a' or 
              mode == 'x'):
            if mode == 'w5':
                mode = 'w'
            try:
                self._file = self.h5.File(self._filename, mode, **kwargs)
            except Exception as error:
                raise NeXusError("'%s' cannot be opened by h5py" 
                                 % self._filename)
            self._mode = 'rw'
        else:
            if mode == 'rw' or mode == 'r+':
                self._mode = 'rw'
                mode = 'r+'
            else:
                self._mode = 'r'
            if os.path.exists(name):
                try:
                    self._file = self.h5.File(self._filename, mode, **kwargs)
                except Exception as error:
                    raise NeXusError("'%s' cannot be opened by h5py" 
                                     % self._filename)
            else:
                raise NeXusError("'%s' does not exist" % name)
        self._file.close()

    def __repr__(self):
        return '<NXFile "%s" (mode %s)>' % (os.path.basename(self._filename),
                                            self._mode)

    def __getattr__(self, name):
        """Return an attribute of the h5py File if not defined by NXFile"""
        return getattr(self.file, name)

    def __getitem__(self, key):
        """Return an object from the NeXus file using its path."""
        return self.file.get(key)

    def __setitem__(self, key, value):
        """Set the value of an object defined by its path in the NeXus file."""
        self.file[key] = value

    def __delitem__(self, key):
        """ Delete an object from the file. """
        del self.file[key]

    def __contains__(self, key):
        """Implement 'k in d' test for entries in the file."""
        return self.file.__contains__(key)

    def __enter__(self):
        """Open and, optionally, lock a NeXus file for multiple operations.

        Returns
        -------
        NXFile
            Current NXFile instance.
        """
        if self._with_count == 0:
            self.acquire_lock()
            self.open()
        self._with_count += 1
        return self

    def __exit__(self, *args):
        """Close the NeXus file and, if necessary, release the lock."""
        if self._with_count == 1:
            self.close()
            self.release_lock()
        self._with_count -= 1

    def __del__(self):
        """Close the file, release any lock, and delete the NXFile instance."""
        self.close()
        self.release_lock()

    @property
    def root(self):
        """Return the root group of the NeXus file."""
        return self._root
    
    @property
    def mtime(self):
        """Return the modification time of the NeXus file."""
        return os.path.getmtime(self._filename)
    
    @property
    def lock(self):
        """Return the NXLock instance to be used in file locking.

        The global variable, `NX_LOCK`, defines the default timeout in
        seconds of attempts to acquire the lock. If it is set to 0, the 
        NXFile object is not locked by default. The `lock` property can 
        be set to turn on file locking, either by setting it to a new
        timeout value or by setting it to `True`, in which case a default 
        timeout of 10 seconds is used.

        Notes
        -----
        The default value of `NX_LOCK` can be set using the `nxsetlock` 
        function.

        Returns
        -------
        NXLock
            Instance of the file lock.
        """
        return self._lock

    @lock.setter
    def lock(self, value):
        if self._lock is None:
            self._lock = NXLock(self._filename, timeout=NX_LOCK)
        if value is False or value is None or value == 0:
            self._lock.timeout = 0
        else:
            if value is True:
                if NX_LOCK:
                    timeout = NX_LOCK
                else:
                    timeout = 10
            else:
                timeout = value
            self._lock.timeout=timeout

    @property
    def locked(self):
        """Return True if a file lock is active in the current process."""
        return self._lock is not None and self._lock.locked

    @property
    def lock_file(self):
        """Return the name of the file used to establish the lock."""
        if self._lock is None:
            self._lock = NXLock(self._filename, timeout=NX_LOCK)
        return self._lock.lock_file

    def acquire_lock(self, timeout=None):
        """Acquire the file lock.

        This uses the NXLock instance returned by `self.lock`.
        
        Parameters
        ----------
        timeout : int, optional
            Timeout for attempts to acquire the lock, by default None.
        """
        if self.locked and self.is_locked():
            return
        if self._lock is None:
            if timeout is not None:
                self.lock = timeout
            elif NX_LOCK:
                self.lock = NX_LOCK
            elif self.is_locked():
                self.lock = True
            if self._lock is None:
                return
        self._lock.acquire()

    def release_lock(self):
        """Release the lock acquired by the current process."""
        if self.locked:
            self._lock.release()

    def wait_lock(self, timeout=True):
        """Wait for a file lock created by an external process to be cleared.
        
        Parameters
        ----------
        timeout : bool or int, optional
            The value, in seconds, of the time to wait. If set to `True`, a
            default value of 10 seconds is used.
        """
        self.lock = timeout
        NXLock(self._filename, timeout=timeout).wait()

    def clear_lock(self, timeout=True):
        """Clear the file lock whether created by this or another process.

        Notes
        -----
        Since the use of this function implies that another process is 
        accessing this file, file locking is turned on for future 
        input/output. The `timeout` value applies to future access. The
        existing lock is cleared immediately.
        
        Parameters
        ----------
        timeout : bool or int, optional
            The value, in seconds, of the time to wait for future file locks. 
            If set to `True`, a default value of 10 seconds is used.
        """
        if self.is_locked():
            self.lock = timeout
            self._lock.clear()

    def is_locked(self):
        """Return True if a lock file exists for this NeXus file."""
        return os.path.exists(self.lock_file)

    def get(self, *args, **kwargs):
        """Return the value defined by the `h5py` object path."""
        return self.file.get(*args, **kwargs)

    def open(self, **kwargs):
        """Open the NeXus file for input/output."""
        if not self.is_open():
            if self._mode == 'rw':
                self._file = self.h5.File(self._filename, 'r+', **kwargs)
            else:
                self._file = self.h5.File(self._filename, self._mode, **kwargs)
            self.nxpath = '/'

    def close(self):
        """Close the NeXus file.
        
        Notes
        -----
        The file modification time of the root object is updated.
        """
        if self.is_open():
            self._file.close()
        if self._root:
            self._root._mtime = self.mtime

    def is_open(self):
        """Return True if the file is open for input/output in h5py."""
        if self._file is not None:
            return True if self._file.id.valid else False
        else:
            return False

    def readfile(self):
        """Read the NeXus file and return a tree of NeXus objects.

        The hierarchy is traversed using `nxpath` to record the current 
        location within the file. It is initially set to the root object, 
        *i.e.*, '/'.

        Notes
        -----
        This lazily loads all the file objects, *i.e.*, the values stored in
        large dataset arrays are not read until they are needed.
        """
        _mode = self._mode
        self._mode = 'r'
        self.nxpath = '/'
        root = self._readgroup('root')
        root._group = None
        root._file = self
        root._filename = self._filename
        root._mode = self._mode = _mode
        root._file_modified = False
        self._root = root
        return root

    def _readattrs(self):
        """Read an object's attributes
        
        Returns
        -------
        dict
            Dictionary of attribute values.
        """
        item = self.get(self.nxpath)
        if item is not None:
            attrs = {}
            for key in item.attrs:
                try:
                    attrs[key] = item.attrs[key]
                except Exception:
                    attrs[key] = None
            return attrs
        else:
            return {}

    def _readchildren(self):
        """Read the children of the group defined by the current path.
        
        Returns
        -------
        list of NXfield or NXgroup
            The objects contained within the current group.
        """
        children = {}
        items = self[self.nxpath].items()
        for name, value in items:
            self.nxpath = self.nxpath + '/' + name
            if isinstance(value, self.h5.Group):
                children[name] = self._readgroup(name)
            elif isinstance(value, self.h5.Dataset):
                children[name] = self._readdata(name)
            else:
                _link = self._readlink(name)
                if _link:
                    children[name] = _link
            self.nxpath = self.nxparent
        return children

    def _readgroup(self, name):
        """Return the group at the current path.
        
        Parameters
        ----------
        name : str
            Name of the group.
        
        Returns
        -------
        NXgroup or NXlinkgroup
            Group or link defined by the current path.
        """
        attrs = self._readattrs()
        nxclass = self._getclass(attrs.pop('NX_class', 'NXgroup'))
        if nxclass == 'NXgroup' and self.nxpath == '/':
            nxclass = 'NXroot'
        children = self._readchildren()
        _target, _filename, _abspath = self._getlink()
        if _target is not None:
            group = NXlinkgroup(nxclass=nxclass, name=name, target=_target,
                                file=_filename, abspath=_abspath)
        else:
            group = NXgroup(nxclass=nxclass, name=name, attrs=attrs)
        for child in children:
            group._entries[child] = children[child]
            children[child]._group = group
        group._changed = True
        return group

    def _readdata(self, name):
        """Read a dataset and return the NXfield or NXlink at the current path.
        
        Parameters
        ----------
        name : str
            Name of the field or link.
        
        Returns
        -------
        NXfield or NXlinkfield
            Field or link defined by the current path.
        """
        _target, _filename, _abspath = self._getlink()
        if _target is not None:
            return NXlinkfield(name=name, target=_target, file=_filename, 
                               abspath=_abspath)
        else:
            value, shape, dtype, attrs = self.readvalues()
            return NXfield(value=value, name=name, dtype=dtype, shape=shape, 
                           attrs=attrs)

    def _readlink(self, name):
        """Read an object that is an undefined link at the current path.
        
        This is usually an external link to a non-existent file. It can also be
        a link to an external file that has not yet been resolved.
        
        Parameters
        ----------
        name : str
            Name of the object link.
        
        Returns
        -------
        NXlink
            Link defined by the current path.
        """
        _target, _filename, _abspath = self._getlink()
        if _target is not None:
            return NXlink(name=name, target=_target, file=_filename, 
                          abspath=_abspath)
        else:
            return None
 
    def _getclass(self, nxclass):
        """Return a valid NeXus class from the object attribute.

        This function converts the `NX_class` attribute of an object in the
        NeXus file and converts it to a valid string. If no attribute is 
        found, the class is set to 'NXgroup'.
        
        Parameters
        ----------
        nxclass : str
            Attribute defining the object class.
        
        Returns
        -------
        str
            Valid NeXus class.
        """
        nxclass = text(nxclass)
        if nxclass is None:
            return 'NXgroup'
        else:
            return nxclass

    def _getlink(self):
        """Return the link target path and filename.
        
        Returns
        -------
        str, str, bool
            Link path, filename, and boolean that is True if an absolute file
            path is given.
        """
        _target, _filename, _abspath = None, None, False
        if self.nxpath != '/':
            _link = self.get(self.nxpath, getlink=True)
            if isinstance(_link, h5.ExternalLink):
                _target, _filename = _link.path, _link.filename
                _abspath = os.path.isabs(_filename)
            elif isinstance(_link, h5.SoftLink):
                _target = _link.path
            elif 'target' in self.attrs:
                _target = text(self.attrs['target'])
                if not _target.startswith('/'):
                    _target = '/' + _target
                if _target == self.nxpath:
                    _target = None
        return _target, _filename, _abspath

    def writefile(self, root):
        """Write the whole NeXus tree to the file.

        The file is assumed to start empty.
        
        Parameters
        ----------
        root : NXroot
            Root group of the NeXus tree.
        """
        links = []
        self.nxpath = ""
        for entry in root.values():
            links += self._writegroup(entry)
        self._writelinks(links)
        if len(root.attrs) > 0:
            self._writeattrs(root.attrs)
        root._filename = self._filename
        self._root = root
        self._rootattrs()

    def _writeattrs(self, attrs):
        """Write the attributes for the group or field with the current path.

        The attributes are stored as NXattr entries in an AttrDict dictionary.
        The attribute values are contained in the NXattr `nxdata` attribute.

        Parameters
        ----------
        attrs : AttrDict
            Dictionary of group or field attributes.
        """
        if self[self.nxpath] is not None:
            for name, value in attrs.items():
                if value.nxdata is not None:
                    self[self.nxpath].attrs[name] = value.nxdata

    def _writegroup(self, group):
        """Write a group and its children to the NeXus file.

        Internal NXlinks cannot be written until the linked group is created, 
        so this routine returns the set of links that need to be written.
        Call writelinks on the list.
        
        Parameters
        ----------
        group : NXgroup
            NeXus group to be written.
        
        Returns
        -------
        list
            List of links.
        """
        if group.nxpath != '' and group.nxpath != '/':
            self.nxpath = self.nxpath + '/' + group.nxname
            if group.nxname not in self[self.nxparent]:
                if group._target is not None:
                    if group._filename is not None:
                        self.nxpath = self.nxparent
                        self._writeexternal(group)
                        self.nxpath = self.nxparent
                        return []
                else:
                    self[self.nxparent].create_group(group.nxname)
            if group.nxclass and group.nxclass != 'NXgroup':
                self[self.nxpath].attrs['NX_class'] = group.nxclass
        links = []
        self._writeattrs(group.attrs)
        if group._target is not None:
            links += [(self.nxpath, group._target)]
        for child in group.values():
            if isinstance(child, NXlink):
                if child._filename is not None:
                    self._writeexternal(child)
                else:
                    links += [(self.nxpath+"/"+child.nxname, child._target)]
            elif isinstance(child, NXfield):
                links += self._writedata(child)
            else:
                links += self._writegroup(child)
        self.nxpath = self.nxparent
        return links

    def _writedata(self, data):
        """Write the field to the NeXus file.

        NXlinks cannot be written until the linked group is created, so
        this routine returns the set of links that need to be written.
        Call writelinks on the list.
        
        Parameters
        ----------
        data : NXfield
            NeXus field to be written to the file.
        
        Returns
        -------
        list
            List of links.
        """
        self.nxpath = self.nxpath + '/' + data.nxname
        # If the data is linked then
        if data._target is not None:
            if data._filename is not None:
                self._writeexternal(data)
                self.nxpath = self.nxparent
                return []
            else:
                path = self.nxpath
                self.nxpath = self.nxparent
                return [(path, data._target)]
        if data._uncopied_data:
            if self.nxpath in self:
                del self[self.nxpath]
            _file, _path = data._uncopied_data
            if _file._filename != self._filename:
                with _file as f:
                    f.copy(_path, self[self.nxparent], name=self.nxpath)
            else:
                self.file.copy(_path, self[self.nxparent], name=self.nxpath)
            data._uncopied_data = None
        elif data._memfile:
            data._memfile.copy('data', self[self.nxparent], name=self.nxpath)
            data._memfile = None
        elif data.nxfile and data.nxfile.filename != self.filename:
            data.nxfile.copy(data.nxpath, self[self.nxparent])
        elif data.dtype is not None:
            if data.nxname not in self[self.nxparent]:
                self[self.nxparent].create_dataset(data.nxname, 
                                                   shape=data.shape, 
                                                   dtype=data.dtype,
                                                   **data._h5opts)
            try:
                if data._value is not None:
                    self[self.nxpath][()] = data._value 
            except NeXusError:
                pass
        self._writeattrs(data.attrs)
        self.nxpath = self.nxparent
        return []

    def _writeexternal(self, item):
        """Create an external link.

        Notes
        -----
        The filename is converted to a path relative to the current NeXus
        file, unless `item._abspath` is set to True.
        
        Parameters
        ----------
        item : NXlinkgroup or NXlinkfield
            NeXus group or field containing the link target and filename.
        """
        self.nxpath = self.nxpath + '/' + item.nxname
        if item._abspath:
            filename = item.nxfilename
        elif os.path.isabs(item._filename):
            filename = os.path.relpath(os.path.realpath(item._filename), 
                           os.path.dirname(os.path.realpath(self.filename)))
        else:
            filename = item._filename
        self[self.nxpath] = self.h5.ExternalLink(filename, item._target)
        self.nxpath = self.nxparent

    def _writelinks(self, links):
        """Creates links within the NeXus file.

        These are defined by the set of pairs returned by _writegroup.
        
        Parameters
        ----------
        links : list ot tuples
            List of tuples containing the paths to the links and their targets. 
        """
        # link sources to targets
        for path, target in links:
            if path != target and path not in self['/'] and target in self['/']:
                if 'target' not in self[target].attrs:
                    self[target].attrs['target'] = target
                self[path] = self[target]

    def readpath(self, path):
        """Read the object defined by the given path.
        
        Parameters
        ----------
        path : str
            Path to the NeXus object.
        
        Returns
        -------
        NXgroup or NXfield
            The group or field defined by the specified path.
        """
        self.nxpath = path
        return self.readitem()

    def readitem(self):
        """Read the object defined by the current path.
        
        Returns
        -------
        NXgroup or NXfield
            The group or field defined by the current path.
        """
        item = self.get(self.nxpath)
        if isinstance(item, self.h5.Group):
            return self._readgroup(self.nxname)
        else:
            return self._readdata(self.nxname)

    def readvalues(self, attrs=None):
        """Read the values of the field at the current path.

        Notes
        -----
        The values are only read if the array size is less than 10000.
        
        Parameters
        ----------
        attrs : dict, optional
            Attribute of the field, by default None
        
        Returns
        -------
        tuple
            Value, shape, dtype, and attributes of the field 
        """
        field = self.get(self.nxpath)
        if field is None:
            return None, None, None, {}
        shape, dtype = field.shape, field.dtype
        #Read in the data if it's not too large
        if np.prod(shape) < 1000:# i.e., less than 1k dims
            try:
                value = self.readvalue(self.nxpath)
            except Exception as error:
                value = None
        else:
            value = None
        if attrs is None:
            attrs = self.attrs
            if 'NX_class' in attrs and text(attrs['NX_class']) == 'SDS':
                attrs.pop('NX_class')
        return value, shape, dtype, attrs

    def readvalue(self, path, idx=()):
        """Return the array stored in the NeXus file at the specified path.
        
        Parameters
        ----------
        path : str
            Path to the NeXus field.
        idx : tuple, optional
            Slice of field to be returned, by default the whole field.
        
        Returns
        -------
        array_like or str
            Array or string stored in the NeXus file at the current path.
        """
        field = self.get(path)
        if field is not None:
            return field[idx]
        return None

    def writevalue(self, path, value, idx=()):
        """Write a field value at the specified path in the file.
        
        Parameters
        ----------
        path : str
            Specified path
        value : NXfield or array-like
            Value to be written at the specified path.
        idx : tuple, optional
            Slice to be written, by default the whole field.
        """
        self[path][idx] = value

    def move(self, source, destination):
        """Move an object defined by its path to another location.

        This is an interface to the `h5py.Group` move function.
        
        Parameters
        ----------
        source : str
            Path to the object to be moved.
        destination : str
            Path of the new destination.
        """
        self.file.move(source, destination)

    def copy(self, source, destination, **kwargs):
        """Copy an object defined by its path to another location.
        
        This is an interface to the `h5py.Group` copy function. All the
        `h5py` keyword arguments can be used.
        
        Parameters
        ----------
        source : str
            Path to the object to be copied.
        destination : str
            Path of the new copy.
        """
        self.file.copy(source, destination, **kwargs)

    def copyfile(self, input_file, **kwargs):
        """Copy an entire NeXus file to another file.

        All the `h5py.Group.copy()` keyword arguments can be used.
        
        Parameters
        ----------
        input_file : NXFile
            NeXus file to be copied.
        """
        for entry in input_file['/']:
            input_file.copy(entry, self['/'], **kwargs) 
        self._rootattrs()

    def _rootattrs(self):
        """Write root attributes to the NeXus file."""
        from datetime import datetime
        self.file.attrs['file_name'] = self.filename
        self.file.attrs['file_time'] = datetime.now().isoformat()
        self.file.attrs['HDF5_Version'] = self.h5.version.hdf5_version
        self.file.attrs['h5py_version'] = self.h5.version.version
        from .. import __version__
        self.file.attrs['nexusformat_version'] = __version__

    def update(self, item):
        """Update the specifed object in the NeXus file.

        Notes
        -----
        If the specified object is an NXobject, it is assumed to contain the
        path, file, and keyword arguments to be used to copy it to the 
        specified item path, using the `h5py.Group` copy function. 
        
        Parameters
        ----------
        item : NXgroup or NXfield or AttrDict
            Group, field or attributes to be updated in the NeXus file.
        """
        self.nxpath = item.nxpath
        if isinstance(item, AttrDict):
            self._writeattrs(item)
        else:
            self.nxpath = self.nxparent
            if isinstance(item, NXlink):
                if item._filename is None:
                    self._writelinks([(item.nxpath, item._target)])
                else:
                    self._writeexternal(item)
            elif isinstance(item, NXfield):
                self._writedata(item)
            elif isinstance(item, NXgroup):
                links = self._writegroup(item)
                self._writelinks(links)
            elif isinstance(item, NXobject):
                if isinstance(item._copyfile, NXFile):
                    with item._copyfile as f:
                        self.copy(f[item._copypath], item.nxpath, **item._attrs)
                    item = self.readpath(item.nxpath)
                    if self.nxparent == '/':
                        group = self._root
                    else:
                        group = self._root[self.nxparent]
                    group._entries[item.nxname] = item
                    group[item.nxname]._group = group
            self.nxpath = item.nxpath

    def reload(self):
        """Reload the entire NeXus file.

        This may be necessary if another process has modified the file on disk.
        """
        self.nxpath = '/'
        self._root._entries = self._readchildren()
        for entry in self._root._entries:
            self._root._entries[entry]._group = self._root
        self._root._changed = True
        self._root._file_modified = False

    def rename(self, old_path, new_path):
        """Rename an object defined by its path to a new path.
        
        Parameters
        ----------
        old_path : str
            Old path to the NeXus object.
        new_path : str
            New path to the NeXus object.
        """
        if old_path != new_path:
            self.file['/'].move(old_path, new_path)

    @property
    def filename(self):
        """The file name on disk."""
        return self.file.filename

    @property
    def file(self):
        """The h5py File object, which is opened if necessary."""
        if not self.is_open():
            self.open()
        return self._file

    @property
    def mode(self):
        """File mode of the NeXus file."""
        return self._mode

    @mode.setter
    def mode(self, mode):
        if mode == 'rw' or mode == 'r+':
            self._mode = 'rw'
        else:
            self._mode = 'r'   
        self.close()

    @property
    def attrs(self):
        """Attributes of the object defined by the current path."""
        return self._readattrs()

    @property
    def nxpath(self):
        """Current path in the NeXus file."""
        return self._path.replace('//','/')

    @nxpath.setter
    def nxpath(self, value):
        self._path = value.replace('//','/')

    @property
    def nxparent(self):
        """Path to the parent of the current path."""
        return '/' + self.nxpath[:self.nxpath.rfind('/')].lstrip('/')

    @property
    def nxname(self):
        """Name of the object at the current path"""
        return self.nxpath[self.nxpath.rfind('/')+1:]


def _makeclass(cls, bases=None):
    """Create a new subclass of the NXgroup class.
    
    Parameters
    ----------
    bases : tuple of classes, optional
        Superclasses of the new class, by default :class:`NXgroup`.
    
    Returns
    -------
    type
        New subclass.
    """
    docstring = """
                %s group. This is a subclass of the NXgroup class.

                See the NXgroup documentation for more details.
                """ % cls
    if bases is None:
        bases = (NXgroup,)
    return type(str(cls), bases, {'_class':cls, '__doc__':docstring})


def _getclass(cls, link=False):
    """Return class based on the name or type.
    
    Parameters
    ----------
    link : bool, optional
        True if the class is also a :class:`NXlink` subclass, by default False.
    
    Returns
    -------
    type
        Class object.
    """
    if isinstance(cls, type):
        cls = cls.__name__
    if not cls.startswith('NX'):
        return type(object)
    elif cls in globals() and (not link or cls.startswith('NXlink')):
        return globals()[cls]
    if cls != 'NXlink' and cls.startswith('NXlink'):
        link = True
        cls = cls.replace('NXlink', 'NX')
    if link:
        if cls in globals():
            bases = (NXlinkgroup, globals()[cls])
            cls = cls.replace('NX', 'NXlink')
            globals()[cls] = _makeclass(cls, bases)
        else:
            raise NeXusError("'%s' is not a valid NeXus class" % cls)
    else:
        globals()[cls] = _makeclass(cls, (NXgroup,))
    return globals()[cls]


def _getvalue(value, dtype=None, shape=None):
    """Return the value of a field or attribute based on a Python value.

    If 'dtype' and/or 'shape' are specified as input arguments, the value is 
    converted to the given dtype and/or reshaped to the given shape. Otherwise, 
    the dtype and shape are determined from the value.

    If the value is a masked array, the returned value is only returned as a 
    masked array if some of the elements are masked.
   
    Parameters
    ----------
    value
        Input Python value
    dtype : dtype or str, optional
        Required dtype of value, by default None
    shape : tuple, optional
        Required shape of value, by default None
    
    Returns
    -------
    tuple
        Value, dtype, and shape for creation of new field or attribute.
    """
    dtype, shape = _getdtype(dtype), _getshape(shape)
    if isinstance(value, NXfield) or isinstance(value, NXattr):
        value = value.nxvalue
    if value is None:
        return None, dtype, shape
    elif is_text(value):
        if shape is not None and shape != ():
            raise NeXusError("The value is incompatible with the shape")
        if dtype is not None:
            try:
                _dtype = _getdtype(dtype)
                if _dtype.kind == 'S':
                    value = text(value).encode('utf-8')
                return np.array(value, dtype=_dtype).item(), _dtype, ()
            except Exception:
                raise NeXusError("The value is incompatible with the dtype")
        else:
            _value = text(value)
            if _value == u'':
                _value = u' '
            return _value, string_dtype, ()
    elif isinstance(value, np.ndarray):
        if isinstance(value, np.ma.MaskedArray):
            if value.count() < value.size: #some values are masked
                _value = value
            else:
                _value = np.asarray(value)
        else:
            _value = np.asarray(value) #convert subclasses of ndarray
    else:
        try:
            _value = [np.asarray(v) for v in value]
            if len(set([v.shape for v in _value])) > 1:
                raise NeXusError(
                    "Cannot assign an iterable with items of multiple shapes")
            _value = np.asarray(_value)
        except TypeError:
            _value = np.asarray(value)
        if _value.dtype.kind == 'S' or _value.dtype.kind == 'U':
            _value = _value.astype(string_dtype)
    if dtype is not None:
        if isinstance(value, np.bool_) and dtype != np.bool_:
            raise NeXusError(
                "Cannot assign a Boolean value to a non-Boolean field")
        elif isinstance(_value, np.ndarray):
            try:
                _value = _value.astype(dtype)
            except:
                raise NeXusError("The value is incompatible with the dtype")
    if shape is not None and isinstance(_value, np.ndarray):
        try:
            _value = _value.reshape(shape)
        except ValueError:
            raise NeXusError("The value is incompatible with the shape")
    if _value.shape == () and not np.ma.is_masked(_value):
        return _value.item(), _value.dtype, _value.shape
    else:
        return _value, _value.dtype, _value.shape


def _getdtype(dtype):
    """Return a valid h5py dtype.

    This converts string dtypes to the special HDF5 dtype for variable length 
    strings. Other values are checked against valid Numpy dtypes.
    
    Parameters
    ----------
    dtype : dtype
        Proposed datatype of an NXfield.
    
    Returns
    -------
    dtype
        Valid dtype for storing in an HDF5 file.
    """
    if dtype is None:
        return None
    elif is_text(dtype) and dtype == 'char':
        return string_dtype
    else:
        try:
            _dtype = np.dtype(dtype)
            if _dtype.kind == 'U':
                return string_dtype
            else:
                return _dtype
        except TypeError:
            raise NeXusError("Invalid data type: %s" % dtype)


def _getshape(shape, maxshape=False):
    """Return valid shape tuple.

    The returned shape tuple will contain integer values, unless maxshape is
    True, in which case, values of None are allowed.
    
    Parameters
    ----------
    shape : tuple of int
        Proposed new shape
    maxshape : bool, optional
        True if values of None are permitted in a shape element,
        by default False
    
    Returns
    -------
    tuple of int
        Valid shape tuple.
    """
    if shape is None:
        return None
    else:
        try:
            if not is_iterable(shape):
                shape = [shape]       
            if maxshape:
                return tuple([None if i is None else int(i) for i in shape])
            elif None in shape:
                return None
            else:
                return tuple([int(i) for i in shape])
        except ValueError:
            raise NeXusError("Invalid shape: %s" % str(shape))

    
def _getmaxshape(maxshape, shape):
    """Return maximum shape if compatible with the specified shape.

    This raises a NeXusError if the length of the shapes do not match or if
    any of the elements in maxshape are smaller than the corresponding 
    element in shape. If maxshape has a size of 1, an empty tuple is returned.
    
    Parameters
    ----------
    maxshape : tuple of int
        Proposed maximum shape of the array
    shape : tuple of int
        Current shape of the array
    
    Returns
    -------
    tuple of int
        Maximum shape
    """
    maxshape, shape = _getshape(maxshape, maxshape=True), _getshape(shape)
    if maxshape is None or shape is None:
        return None
    else:
        if maxshape == (1,) and shape == ():
            return ()
        elif len(maxshape) != len(shape):
            raise NeXusError(
            "Number of dimensions in maximum shape does not match the field")
        else:
            if _checkshape(shape, maxshape):
                return maxshape
            else:
                raise NeXusError(
                    "Maximum shape must be larger than the field shape")


def _checkshape(shape, maxshape):
    """Return True if the shape is consistent with the maximum allowed shape.

    Each element of shape must be less than or equal to the 
    corresponding element of maxshape, unless the latter is set to None, in 
    which case the value of the shape element is unlimited.
    
    Parameters
    ----------
    shape : tuple of int
        Shape to be checked.
    maxshape : tuple of int
        Maximum allowed shape
    
    Returns
    -------
    bool
        True if the shape is consistent.
    """
    for i, j in [(_i, _j) for _i, _j in zip(maxshape, shape)]:
        if i is not None and i < j:
            return False
    return True

    
def _getsize(shape):
    """Return the total size of the array with the specified shape.

    If the shape is None, a size of 1 is returned.
    
    Parameters
    ----------
    shape : tuple of int
        Shape of the array.
    
    Returns
    -------
    int
        Size of the array
    """
    if shape is None:
        return 1
    else:
        try:
            return np.prod(shape)
        except Exception:
            return 1

    
def _readaxes(axes):
    """Return a list of axis names stored in the 'axes' attribute.

    If the input argument is a string, the names are assumed to be separated 
    by a delimiter, which can be white space, a comma, or a colon. If it is
    a list of strings, they are converted to Unicode strings.
    
    Parameters
    ----------
    axes : str or list of str
        Value of 'axes' attribute defining the plotting axes.
    
    Returns
    -------
    list of str
        Names of the axis fields.
    """
    if is_text(axes):
        return list(re.split(r'[,:; ]', 
                    text(axes).strip('[]()').replace('][', ':')))
    else:
        return [text(axis) for axis in axes]


class AttrDict(dict):
    """A dictionary class used to assign and return values to NXattr instances.
    
    This is used to control the initialization of the NXattr objects and the
    return of their values. For example, attributes that contain string or byte
    arrays are returned as lists of (unicode) strings. Size-1 arrays are 
    returned as scalars. The 'get' function can be used to return the original 
    array. If the attribute are stored in a NeXus file with read/write access,
    their values are automatically updated.
    
    Parameters
    ----------
    parent : NXfield or NXgroup
        The field or group to which the attributes belong.
    attrs : dict
        A dictionary containing the first set of attributes.   
    """

    def __init__(self, parent=None, attrs=None):
        super(AttrDict, self).__init__()
        self._parent = parent
        if attrs is not None:
            self._setattrs(attrs)

    def _setattrs(self, attrs):
        for key, value in attrs.items():
            super(AttrDict, self).__setitem__(key, NXattr(value))
    
    def __getitem__(self, key):
        """Returns the value of the requested NXattr object."""
        return super(AttrDict, self).__getitem__(key).nxvalue

    def __setitem__(self, key, value):
        """Creates a new entry in the dictionary."""
        if value is None:
            return
        elif isinstance(self._parent, NXobject):
            if self._parent.nxfilemode == 'r':
                raise NeXusError("NeXus file opened as readonly")
            elif self._parent.is_linked():
                raise NeXusError("Cannot modify an item in a linked group")
        if isinstance(value, NXattr):
            super(AttrDict, self).__setitem__(text(key), value)
        else:
            super(AttrDict, self).__setitem__(text(key), NXattr(value))
        if isinstance(self._parent, NXobject):
            self._parent.set_changed()
            if self._parent.nxfilemode == 'rw':
                with self._parent.nxfile as f:
                    f.update(self)

    def __delitem__(self, key):
        """Deletes an entry from the dictionary."""
        if isinstance(self._parent, NXobject):
            if self._parent.nxfilemode == 'r':
                raise NeXusError("NeXus file opened as readonly")
            elif self._parent.is_linked():
                raise NeXusError("Cannot modify an item in a linked group")
        super(AttrDict, self).__delitem__(key)
        if isinstance(self._parent, NXobject):
            self._parent.set_changed()
            if self._parent.nxfilemode == 'rw':
                with self._parent.nxfile as f:
                    f.nxpath = self._parent.nxpath
                    del f[f.nxpath].attrs[key]

    @property
    def nxpath(self):
        """The path to the NeXus field or group containin the attributes."""
        return self._parent.nxpath

class NXattr(object):
    """Class for NeXus attributes of a NXfield or NXgroup object.

    Attributes
    ----------
    nxvalue : str, scalar, or array-like
        The value of the NeXus attribute modified as described below.
    nxdata : str, scalar, or array-like
        The unmodified value of the NeXus attribute.
    dtype : str
        The data type of the NeXus attribute value.
    shape : tuple
        The shape of the NeXus attribute value.

    Notes
    -----
    NeXus attributes are stored in the 'attrs' dictionary of the parent object,
    NXfield or NXgroup, but can often be referenced or assigned using the
    attribute name as if it were an object attribute.

    For example, after assigning the NXfield, the following three attribute
    assignments are all equivalent::

        >>> entry.sample.temperature = NXfield(40.0)
        >>> entry.sample.temperature.attrs['units'] = 'K'
        >>> entry.sample.temperature.units = NXattr('K')
        >>> entry.sample.temperature.units = 'K'

    The last version above is only allowed for NXfield attributes and is not 
    allowed if the attribute has the same name as one of the following
    internally defined attributes, i.e.,

    ['entries', 'attrs', 'dtype','shape']

    or if the attribute name begins with 'nx' or '_'. It is only possible to
    reference attributes with one of the proscribed names using the 'attrs'
    dictionary.
    """

    def __init__(self, value=None, dtype=None, shape=None):
        if isinstance(value, NXattr) or isinstance(value, NXfield):
            value = value.nxdata
        elif isinstance(value, NXgroup):
            raise NeXusError("A data attribute cannot be a NXgroup")
        self._value, self._dtype, self._shape = _getvalue(value, dtype, shape)

    def __str__(self):
        return text(self.nxvalue)

    def __unicode__(self):
        return text(self.nxvalue)

    def __repr__(self):
        if (self.dtype is not None and 
            (self.shape == () or self.shape == (1,)) and 
            (self.dtype.type == np.string_ or self.dtype.type == np.str_ or 
             self.dtype == string_dtype)):
            return "NXattr('%s')" % self
        else:
            return "NXattr(%s)" % self

    def __eq__(self, other):
        """Returns true if the values of the two attributes are the same."""
        if id(self) == id(other):
            return True
        elif isinstance(other, NXattr):
            return self.nxvalue == other.nxvalue
        else:
            return self.nxvalue == other

    def __hash__(self):
        return id(self)

    @property
    def nxvalue(self):
        """The attribute value for use in Python scripts.
        
        This is the value stored in the NeXus file, with the following
        exceptions.
            1) Size-1 arrays are returned as scalars.
            2) String or byte arrays are returns as a list of strings.
        
        Notes
        -----
        If unmodified values are required, use the 'nxdata' property.
        """
        if self._value is None:
            return ''
        elif (self.dtype is not None and
            (self.dtype.type == np.string_ or self.dtype.type == np.str_ or 
             self.dtype == string_dtype)):
            if self.shape == ():
                return text(self._value)
            elif self.shape == (1,):
                return text(self._value[0])
            else:
                return [text(value) for value in self._value[()]]
        elif self.shape == (1,):
            return self._value.item()
        else:
            return self._value

    @property
    def nxdata(self):
        """The attribute value as stored in the NeXus file."""
        return self._value

    @property
    def dtype(self):
        """The attribute dtype"""
        return self._dtype

    @property
    def shape(self):
        """The attribute shape."""
        try:
            return tuple([int(i) for i in self._shape])
        except (TypeError, ValueError):
            return ()


_npattrs = list(filter(lambda x: not x.startswith('_'), np.ndarray.__dict__))


class NXobject(object):

    """Abstract base class for elements in NeXus files.

    The object has a subclass of NXfield, NXgroup, or one of the NXgroup
    subclasses. Child nodes should be accessible directly as object attributes.
    Constructors for NXobject objects are defined by either the NXfield or
    NXgroup classes.

    Attributes
    ----------
    nxclass : str
        The class of the NXobject. NXobjects can have class NXfield, NXgroup, or
        be one of the NXgroup subclasses.
    nxname : str
        The name of the NXobject. Since it is possible to reference the same
        Python object multiple times, this is not necessarily the same as the
        object name. However, if the object is part of a NeXus tree, this will
        be the attribute name within the tree.
    nxgroup : NXgroup
        The parent group containing this object within a NeXus tree. If the
        object is not part of any NeXus tree, it will be set to None.
    nxpath : str
        The path to this object with respect to the root of the NeXus tree. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.
    nxroot : NXgroup
        The root object of the NeXus tree containing this object. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.
    nxfile : NXFile
        The file handle of the root object of the NeXus tree containing this
        object.
    nxfilename : str
        The file name of NeXus object's tree file handle.
    attrs : dict
        A dictionary of the NeXus object's attributes.
    """

    _class = "unknown"
    _name = "unknown"
    _group = None
    _attrs = AttrDict()
    _file = None
    _filename = None
    _abspath = False
    _target = None
    _external = None
    _mode = None
    _value = None
    _copyfile = None
    _copypath = None
    _memfile = None
    _uncopied_data = None
    _changed = True
    _backup = None
    _file_modified = False
    _smoothing = None

    def __init__(self, *args, **kwargs):
        self._name = kwargs.pop("name", None)
        self._class = kwargs.pop("nxclass", NXobject)
        self._group = kwargs.pop("group", None)
        self._copyfile = kwargs.pop("nxfile", None)
        self._copypath = kwargs.pop("nxpath", None)
        self._attrs = kwargs             

    def __getstate__(self):
        result = self.__dict__.copy()
        hidden_keys = [key for key in result if key.startswith('_')]
        needed_keys = ['_class', '_name', '_group', '_target', 
                       '_entries', '_attrs', '_filename', '_mode', 
                       '_dtype', '_shape', '_value', '_h5opts', '_changed']
        for key in hidden_keys:
            if key not in needed_keys:
                del result[key]
        return result

    def __setstate__(self, dict):
        self.__dict__ = dict

    def __str__(self):
        return "%s" % self.nxname

    def __repr__(self):
        return "NXobject('%s')" % (self.nxname)

    def __bool__(self):
        """Return confirmation that the object exists."""
        return True

    __nonzero__ = __bool__

    def __contains__(self, key):
        return False

    def _setattrs(self, attrs):
        for k,v in attrs.items():
            self._attrs[k] = v

    def walk(self):
        if False: 
            yield

    def _str_name(self, indent=0):
        return " " * indent + self.nxname

    def _str_attrs(self, indent=0):
        names = sorted(self.attrs)
        result = []
        for k in names:
            txt1 = u" " * indent
            txt2 = u"@" + k + " = "
            txt3 = text(self.attrs[k])
            if len(txt3) > 50:
                txt3 = txt3[:46] + '...'
            if is_text(self.attrs[k]):
                txt3 =  u"'" + txt3 + "'"
            else:
                txt3 = txt3
            txt = (txt1 + txt2 + txt3).replace("u'", "'")
            try:
                txt = txt[:txt.index('\n')]+'...'
            except ValueError:
                pass
            result.append(txt)
        return "\n".join(result)

    def _str_tree(self, indent=0, attrs=False, recursive=False):
        result = [self._str_name(indent=indent)]
        if self.attrs and (attrs or indent==0):
            result.append(self._str_attrs(indent=indent+2))
        return "\n".join(result)

    def _get_completion_list(self):
        """Return the attributes and methods for use in autocompletion."""
        return (dir(self) + [attr for attr in object.__dir__(self) 
                             if not attr.startswith('_')])

    def dir(self, attrs=False, recursive=False):
        """Print the group directory.

        The directory is a list of NeXus objects within this group, either NeXus
        groups or NXfield data. If 'attrs' is True, NXfield attributes are
        displayed. If 'recursive' is True, the contents of child groups are also
        displayed.

        Parameters
        ----------
        attrs : bool, optional
            Display attributes in the directory if True, by default False.
        recursive : bool, optional
            Display the directory contents recursively if True, by default 
            False.
        """
        print(self._str_tree(attrs=attrs, recursive=recursive))

    @property
    def tree(self):
        """Return the directory tree as a string.
        
        The tree contains all child objects of this object and their children.
        It invokes the 'dir' method with 'attrs' set to False and 'recursive'
        set to True.

        Returns
        -------
        str
            String containing the hierarchical structure of the tree.
        """
        return self._str_tree(attrs=True, recursive=True)

    @property
    def short_tree(self):
        """Return a shortened directory tree as a string.
        
        The tree contains all child objects of this object and their children.
        It invokes the 'dir' method with 'attrs' set to False and 'recursive'
        set to True.

        Returns
        -------
        str
            String containing the hierarchical structure of the tree.
        """
        return self._str_tree(attrs=False, recursive=2)

    def rename(self, name):
        """Rename the NeXus object.

        This changes the signal or axes attributes to use the new name if 
        necessary.
        
        Parameters
        ----------
        name : str
            New name of the NeXus object.
        """
        name = text(name)
        if name == self.nxname:
            return
        group = self.nxgroup
        if group is not None:
            if group.nxfilemode == 'r':
                raise NeXusError("NeXus parent group is readonly")
            else:
                signal = group.nxsignal
                axes = group.nxaxes
        elif self.nxfilemode == 'r':
            raise NeXusError("NeXus file opened as readonly")
        old_path = self.nxpath
        if group is not None:
            new_path = group.nxpath + '/' + name
            if not isinstance(self, NXroot) and group.nxfilemode == 'rw':
                with group.nxfile as f:
                    f.rename(old_path, new_path)
            group.entries[name] = group.entries.pop(self._name)
            if self is signal:
                group.nxsignal = self
            elif axes is not None:
                if [x for x in axes if x is self]:
                    group.nxaxes = axes
        self._name = name
        self.set_changed()

    def save(self, filename=None, mode='w-', **kwargs):
        """Save the NeXus object to a data file.
        
        If the object is an NXroot group, this can be used to save the whole
        NeXus tree. If the tree was read from a file and the file was opened as
        read only, then a file name must be specified. Otherwise, the tree is
        saved to the original file.

        An error is raised if the object is an NXroot group from an external 
        file that has been opened as readonly and no file name is specified.

        If the object is not an NXroot, group, a filename must be specified. The
        saved NeXus object is wrapped in an NXroot group (with name 'root') and 
        an NXentry group (with name 'entry'), if necessary, in order to produce 
        a valid NeXus file. Only the children of the object will be saved. This 
        capability allows parts of a NeXus tree to be saved for later use, e.g., 
        to store an NXsample group to be added to another file at a later time. 

        Parameters
        ----------
        filename : str
            Name of the data file.
        mode : str, optional
            Mode for opening the file, by default 'w-'
        
        Returns
        -------
        NXroot
            Tree containing all the NeXus fields and groups saved to the file.
        
        Example
        -------
        >>> data = NXdata(sin(x), x)
        >>> data.save('file.nxs')
        >>> print data.nxroot.tree
        root:NXroot
          @HDF5_Version = 1.8.2
          @NeXus_version = 4.2.1
          @file_name = file.nxs
          @file_time = 2012-01-20T13:14:49-06:00
          entry:NXentry
            data:NXdata
              axis1 = float64(101)
              signal = float64(101)
                @axes = axis1
                @signal = 1              
        >>> root['entry/data/axis1'].units = 'meV'
        >>> root.save()
        """
        if filename:
            if os.path.splitext(filename)[1] not in ['.nxs', '.nx5', '.h5',
                                                     '.hdf', '.hdf5', '.cxi']:
                filename = filename + '.nxs'
            if self.nxclass == "NXroot":
                root = self
            elif self.nxclass == "NXentry":
                root = NXroot(self)
            else:
                root = NXroot(NXentry(self)) 
            if mode != 'w':
                write_mode = 'w-'
            else:
                write_mode = 'w'
            with NXFile(filename, write_mode, **kwargs) as f:
                f.writefile(root)
                root = f._root
                root._file = f
            if mode == 'w' or mode == 'w-':
                root._mode = 'rw'
            else:
                root._mode = mode
            self.set_changed()
            return root
        else:
            raise NeXusError("No output file specified")

    def copy(self, name=None, **kwargs):
        """Returns information allowing the object to be copied.
        
        If no group is specified and the current group is saved to a file, 
        a skeleton group is created with information to be used by a h5py copy.
        This is resolved when the skeleton group is assigned to a parent group. 
        
        Parameters
        ----------
        name : str, optional
            Name of copied object if different from current object.
        **kwargs
            Keyword arguments to be transferred to the h5py copy function.
        Returns
        -------
        NXobject
            NeXus object containing information for subsequent copies.
        """
        if self.nxfilemode is None:
            raise NeXusError("Can only copy objects saved to a NeXus file.")
        if name is None:
            name = self.nxname
        return NXobject(name=name, nxclass=self.nxclass, 
                        nxfile=self.nxfile, nxpath=self.nxfilepath, 
                        **kwargs)

    def update(self):
        """Update the object values in its NeXus file if necessary."""
        if self.nxfilemode == 'rw':
            with self.nxfile as f:
                f.update(self)
        self.set_changed()

    @property
    def changed(self):
        """True if the object has been changed.
        
        This property is for use by external scripts that need to track
        which NeXus objects have been changed.
        """
        return self._changed
    
    def set_changed(self):
        """Set an object's change status to changed."""
        self._changed = True
        if self.nxgroup:
            self.nxgroup.set_changed()
            
    def set_unchanged(self, recursive=False):
        """Set an object's change status to unchanged."""
        if recursive:
            for node in self.walk():
                node._changed = False
        else:
            self._changed = False

    def _setclass(self, cls):
        """Change the object class.

        Parameters
        ----------
        cls : type
            New object class.
        """
        try:
            class_ = _getclass(cls)
            if issubclass(class_, NXobject):
                self.__class__ = class_
                self._class = self.__class__.__name__
                if self._class.startswith('NXlink') and self._class != 'NXlink':
                    self._class = 'NX' + self._class[6:]
        except (TypeError, NameError):
            raise NeXusError("Invalid NeXus class")               
    
    @property
    def nxclass(self):
        """NeXus object class."""
        return text(self._class)

    @nxclass.setter
    def nxclass(self, cls):
        self._setclass(cls)
        self.set_changed()

    @property
    def nxname(self):
        """NeXus object name."""
        return text(self._name)

    @nxname.setter
    def nxname(self, value):
        self.rename(value)

    @property
    def nxgroup(self):
        """Parent group of NeXus object."""
        return self._group

    @nxgroup.setter
    def nxgroup(self, value):
        if isinstance(value, NXgroup):
            self._group = value
        else:
            raise NeXusError("Value must be a valid NeXus group")    

    @property
    def nxpath(self):
        """Path to the object in the NeXus tree."""
        group = self.nxgroup
        if self.nxclass == 'NXroot':
            return "/"
        elif group is None:
            return self.nxname
        elif isinstance(group, NXroot):
            return "/" + self.nxname
        else:
            return group.nxpath+"/"+self.nxname

    @property
    def nxroot(self):
        """NXroot object of the NeXus tree."""
        if self._group is None or isinstance(self, NXroot):
            return self
        elif isinstance(self._group, NXroot):
            return self._group
        else:            
            return self._group.nxroot

    @property
    def nxentry(self):
        """Parent NXentry group of the NeXus object."""
        if self._group is None or isinstance(self, NXentry):
            return self
        elif isinstance(self._group, NXentry):
            return self._group
        else:
            return self._group.nxentry

    @property
    def nxfile(self):
        """NXFile storing the NeXus data."""
        if self._file:
            return self._file
        elif not self.is_external() and self.nxroot._file:
            return self.nxroot._file
        elif self.nxfilename:
            self._file = NXFile(self.nxfilename, self.nxfilemode)
            return self._file
        else:
            return None

    @property
    def nxfilename(self):
        """File name of the NeXus file containing the NeXus object.
        
        If the NeXus object is an external link, this is the filename 
        containing the linked data.
        """
        if self._filename is not None:
            if os.path.isabs(self._filename):
                return self._filename
            elif self._group is not None and self._group.nxfilename is not None:
                return os.path.abspath(
                    os.path.join(os.path.dirname(self._group.nxfilename),
                                 self._filename))
            else:
                return os.path.abspath(self._filename)
        elif self._group is not None:
            return self._group.nxfilename
        else:
            return None

    @property
    def nxfilepath(self):
        """File path containing the NeXus object.

        If the NeXus object is an external link, this is the path to the
        object in the external file.
        """
        if self.nxclass == 'NXroot':
            return "/"
        elif isinstance(self, NXlink):
            return self.nxtarget
        elif self.nxgroup is None:
            return ""
        elif isinstance(self.nxgroup, NXroot):
            return "/" + self.nxname
        elif isinstance(self.nxgroup, NXlink):
            group_path = self.nxgroup.nxtarget
        else:
            group_path = self.nxgroup.nxfilepath
        if group_path:
            return group_path+"/"+self.nxname
        else:
            return self.nxname

    @property
    def nxfullpath(self):
        """String containing the file name and path of the NeXus object."""
        return self.nxfilename+"['"+self.nxfilepath+"']"

    @property
    def nxfilemode(self):
        """Read/write mode of the NeXus file if saved to a file."""
        if self._mode is not None:
            return self._mode
        elif self._group is not None:
            return self._group.nxfilemode
        else:
            return None

    @property
    def nxtarget(self):
        """Target path of an NXlink."""
        return self._target

    @property
    def attrs(self):
        """Dictionary of object attributes."""
        if self._attrs is None:
            self._attrs = AttrDict()
        return self._attrs

    def is_plottable(self):
        """True if the NeXus object is plottable."""
        return False

    def is_modifiable(self):
        _mode = self.nxfilemode
        if _mode is None or _mode == 'rw' and not self.is_linked():
            return True
        else:
            return False 

    def is_linked(self):
        """True if the NeXus object is embedded in a link."""
        if self._group is not None:
            if isinstance(self._group, NXlink):
                return True
            else:
                return self._group.is_linked()
        else:
            return False

    def is_external(self):
        """True if the NeXus object is an external link."""
        return (self.nxfilename is not None and 
                self.nxfilename != self.nxroot.nxfilename)

    def file_exists(self):
        """True if the file containing the NeXus object exists."""
        if self.nxfilename is not None:
            return os.path.exists(self.nxfilename)
        else:
            return True

    def path_exists(self):
        """True if the path to the NeXus object exists."""
        if self.is_external():
            if self.file_exists():
                try:
                    with self.nxfile as f:
                        return self.nxfilepath in f
                except Exception as error:
                    return False
            else:
                return False
        else:
            return True

    def exists(self):
        """True if the NeXus object file and path is accessible."""
        return self.file_exists() and self.path_exists()


class NXfield(NXobject):

    """NeXus field for containing scalars, arrays or strings with attributes.

    NXfields usually consist of arrays of numeric data with associated
    meta-data, the NeXus attributes. The exception is when they contain
    character strings. This makes them similar to Numpy arrays, and this module
    allows the use of NXfields in numerical operations in the same way as Numpy
    arrays. NXfields are technically not a sub-class of the ndarray class, but
    most Numpy operations work on NXfields, returning either another NXfield or,
    in some cases, an `ndarray` that can easily be converted to an NXfield.

    Parameters
    ----------
    value : int, float, array_like or string
        Numerical or string value of the NXfield, which is directly
        accessible as the NXfield attribute 'nxvalue'.
    name : str
        Name of the NXfield. 
    dtype : np.dtype or str
        Data type of the NXfield value. Valid dtypes correspond to standard
        Numpy data types, using names defined by the NeXus API, *i.e.*,
        'float32' 'float64'
        'int8' 'int16' 'int32' 'int64'
        'uint8' 'uint16' 'uint32' 'uint64'
        'char'
        If the data type is not specified, it is determined automatically
        by the data type of the 'value'.
    shape : list of ints
        Shape of the NXfield data. This corresponds to the shape of the 
        Numpy array. Scalars (numeric or string) are stored as zero-rank 
        arrays, for which `shape=()`.
    group : NXgroup
        Parent group of NeXus field.
    attrs : dict
        Dictionary containing NXfield attributes.
    kwargs: dict
        Dictionary containing allowed `h5py.Dataset` keyword arguments, 
        *i.e.*, 'chunks', 'compression', 'compression_opts', 'fillvalue',
        'fletcher32', 'maxshape', 'scaleoffset', and 'shuffle'.

    Attributes
    ----------
    nxclass : str
        The class of the NXobject.
    nxname : string
        The name of the NXfield. Since it is possible to reference the same
        Python object multiple times, this is not necessarily the same as the
        object name. However, if the field is part of a NeXus tree, this will
        be the attribute name within the tree.
    nxgroup : NXgroup
        The parent group containing this field within a NeXus tree. If the
        field is not part of any NeXus tree, it will be set to None.
    dtype : string or Numpy dtype
        The data type of the NXfield value. If the NXfield has been initialized
        but the data values have not been read in or defined, this is a string.
        Otherwise, it is set to the equivalent Numpy dtype.
    shape : list or tuple of ints
        The dimensions of the NXfield data. If the NXfield has been initialized
        but the data values have not been read in or defined, this is a list of
        ints. Otherwise, it is set to the equivalent Numpy shape, which is a
        tuple. Scalars (numeric or string) are stored as Numpy zero-rank arrays,
        for which shape=().
    attrs : dict
        A dictionary of all the NeXus attributes associated with the field.
        These are objects with class NXattr.
    nxdata : scalar, Numpy array or string
        The data value of the NXfield. This is normally initialized using the
        'value' parameter (see above). If the NeXus data is contained
        in a file and the size of the NXfield array is too large to be stored
        in memory, the value is not read in until this attribute is directly
        accessed. Even then, if there is insufficient memory, a value of None
        will be returned. In this case, the NXfield array should be read as a
        series of smaller slabs using 'get'.
    nxpath : string
        The path to this object with respect to the root of the NeXus tree. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.
    nxroot : NXgroup
        The root object of the NeXus tree containing this object. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.

    Notes
    -----
    NeXus attributes are stored in the `attrs` dictionary of the NXfield, but
    can usually be assigned or referenced as if they are Python attributes, as
    long as the attribute name is not the same as one of those listed above.
    This is to simplify typing in an interactive session and should not cause
    any problems because there is no name clash with attributes so far defined
    within the NeXus standard. When writing modules, it is recommended that the
    attributes always be referenced using the `attrs` dictionary if there is
    any doubt.

    1) Assigning a NeXus attribute

       In the example below, after assigning the NXfield, the following three
       NeXus attribute assignments are all equivalent:

        >>> entry['sample/temperature'] = NXfield(40.0)
        >>> entry['sample/temperature'].attrs['units'] = 'K'
        >>> entry['sample/temperature'].units = NXattr('K')
        >>> entry['sample/temperature'].units = 'K'

    2) Referencing a NeXus attribute

       If the name of the NeXus attribute is not the same as any of the Python
       attributes listed above, or one of the methods listed below, or any of
       the attributes defined for Numpy arrays, they can be referenced as if
       they were a Python attribute of the NXfield. However, it is only possible
       to reference attributes with one of the proscribed names using the
       `attrs` dictionary.

        >>> entry['sample/temperature'].tree = 10.0
        >>> entry['sample/temperature'].tree
        temperature = 40.0
          @tree = 10.0
          @units = K
        >>> entry['sample/temperature'].attrs['tree']
        NXattr(10.0)

    Examples
    --------
    The following examples show how fields can usually be treated like Numpy 
    arrays.

        >>> x=NXfield((1.0,2.0,3.0,4.0))
        >>> print x+1
        [ 2.  3.  4.  5.]
        >>> print 2*x
        [ 2.  4.  6.  8.]
        >>> print x/2
        [ 0.5  1.   1.5  2. ]
        >>> print x**2
        [  1.   4.   9.  16.]
        >>> print x.reshape((2,2))
        [[ 1.  2.]
         [ 3.  4.]]
        >>> y=NXfield((0.5,1.5,2.5,3.5))
        >>> x+y
        NXfield(array([1.5, 3.5, 5.5, 7.5]))
        >>> x*y
        NXfield(array([ 0.5,  3. ,  7.5, 14. ]))
        >>> (x+y).shape
        (4,)
        >>> (x+y).dtype
        dtype('float64')

    All these operations return valid NXfield objects containing the same
    attributes as the first NXobject in the expression. The 'reshape' and
    'transpose' methods also return NXfield objects.

    It is possible to use the standard slice syntax.

        >>> x=NXfield(np.linspace(0,10,11))
        >>> x
        NXfield([  0.   1.   2. ...,   8.   9.  10.])
        >>> x[2:5]
        NXfield([ 2.  3.  4.])

    In addition, it is possible to use floating point numbers as the slice
    indices. If one of the indices is not integer, both indices are used to
    extract elements in the array with values between the two index values.

        >>> x=NXfield(np.linspace(0,100.,11))
        >>> x
        NXfield([   0.   10.   20. ...,   80.   90.  100.])
        >>> x[20.:50.]
        NXfield([ 20.  30.  40.  50.])

    The standard Numpy ndarray attributes and methods will also work with
    NXfields, but will return scalars or Numpy arrays.

        >>> x.size
        4
        >>> x.sum()
        10.0
        >>> x.max()
        4.0
        >>> x.mean()
        2.5
        >>> x.var()
        1.25
        >>> x.reshape((2,2)).sum(1)
        NXfield(array([3., 7.]))

    Finally, NXfields are cast as `ndarrays` for operations that require them.
    The returned value will be the same as for the equivalent ndarray
    operation, *e.g.*,

        >>> np.sin(x)
        NXfield(array([ 0.        ,  0.84147098,  0.90929743, ...,  0.98935825,
        0.41211849, -0.54402111]))
        >>> np.sqrt(x)
        NXfield(array([0.        , 1.        , 1.41421356, ..., 2.82842712, 3.,
        3.16227766]))

    """
    properties = ['mask', 'dtype', 'shape', 'chunks', 'compression', 
                  'compression_opts', 'fillvalue', 'fletcher32', 'maxshape', 
                  'scaleoffset', 'shuffle']

    def __init__(self, value=None, name='unknown', shape=None, dtype=None, 
                 group=None, attrs=None, **kwargs):
        self._class = 'NXfield'
        self._name = name
        self._group = group
        self._value, self._dtype, self._shape = _getvalue(value, dtype, shape)
        _size = _getsize(self._shape)
        _h5opts = {}
        _h5opts['chunks'] = kwargs.pop('chunks', 
                                       True if _size>NX_MAXSIZE else None)
        _h5opts['compression'] = kwargs.pop('compression', 
                                            NX_COMPRESSION 
                                            if _size>NX_MAXSIZE else None)
        _h5opts['compression_opts'] = kwargs.pop('compression_opts', None)
        _h5opts['fillvalue'] = kwargs.pop('fillvalue', None)
        _h5opts['fletcher32'] = kwargs.pop('fletcher32', None)
        _h5opts['maxshape'] = _getmaxshape(kwargs.pop('maxshape', None), 
                                           self._shape)
        _h5opts['scaleoffset'] = kwargs.pop('scaleoffset', None)
        _h5opts['shuffle'] = kwargs.pop('shuffle', 
                                        True if _size>NX_MAXSIZE else None)
        self._h5opts = dict((k, v) for (k, v) in _h5opts.items() 
                            if v is not None)
        if attrs is None:
            attrs = {}
        attrs.update(kwargs)
        self._attrs = AttrDict(self, attrs=attrs)
        self._memfile = None
        self._uncopied_data = None
        self.set_changed()

    def __dir__(self):
        return sorted([c for c in dir(super(self.__class__, self)) 
                       if not c.startswith('_')]+list(self.attrs), 
                      key=natural_sort)

    def __repr__(self):
        if self._value is not None:
            return "NXfield(%s)" % repr(self.nxvalue)
        else:
            return "NXfield(shape=%s, dtype=%s)" % (self.shape, self.dtype)

    def __str__(self):
        if self._value is not None:
            return text(self.nxvalue)
        return ""

    def __unicode__(self):
        if self._value is not None:
            return text(self.nxvalue)
        return u""

    def __getattr__(self, name):
        """Return Numpy array attribute or NeXus attributes if not defined."""
        if name in _npattrs:
            return getattr(self.nxdata, name)
        elif name in self.attrs:
            return self.attrs[name]
        else:
            raise AttributeError("'"+name+"' not in "+self.nxpath)

    def __setattr__(self, name, value):
        """Add an attribute to the NXfield's attribute dictionary.
        
        Parameters
        ----------
        name : str
            Name of the field attribute.
        value : str or array-like
            Value to be assigned to the field attribute.

        Notes
        -----
        If the attribute name starts with 'nx' or '_', they are assigned as
        NXfield attributes without further conversions.
        """
        if (name.startswith('_') or name.startswith('nx') or 
            name in self.properties):
            object.__setattr__(self, name, value)
        elif self.is_modifiable():
            self._attrs[name] = value
            self.set_changed()
        elif self.is_linked():
            raise NeXusError("Cannot modify an item in a linked group")
        else:
            raise NeXusError("NeXus file opened as readonly")

    def __delattr__(self, name):
        """Delete an attribute in the NXfield attributes dictionary."""
        if self.is_modifiable() and name in self.attrs:
            del self.attrs[name]
            self.set_changed()
        elif self.is_linked():
            raise NeXusError("Cannot modify an item in a linked group")
        else:
            raise NeXusError("NeXus file opened as readonly")

    def __getitem__(self, idx):
        """Return a slice from the NXfield.

        In most cases, the slice values are applied to the NXfield nxdata array
        and returned within an NXfield object with the same metadata. However,
        if the array is one-dimensional and the index start and stop values
        are real, the nxdata array is returned with values between those limits.
        This is to allow axis arrays to be limited by their actual value. This
        real-space slicing should only be used on monotonically increasing (or
        decreasing) one-dimensional arrays.

        Parameters
        ----------
        idx : slice
            Slice indices.
        
        Returns
        -------
        NXfield
            Field containing the slice values.
        """
        if is_real_slice(idx):
            idx = convert_index(idx, self)
        if self._value is None:
            if self._uncopied_data:
                result = self._get_uncopied_data(idx)
            elif self.nxfilemode:
                result = self._get_filedata(idx)
            elif self._memfile:
                result = self._get_memdata(idx)
                mask = self.mask
                if mask is not None:
                    if isinstance(mask, NXfield):
                        mask = mask[idx].nxdata
                    else:
                        mask = mask[idx]
                    if isinstance(result, np.ma.MaskedArray):
                        result = result.data
                    result = np.ma.array(result, mask=mask)
            elif self.fillvalue:
                result = np.asarray(np.empty(self.shape, dtype=self.dtype)[idx])
                result.fill(self.fillvalue)
            else:
                raise NeXusError(
                    "Data not available either in file or in memory")
            if self.mask is not None:
                result = np.ma.MaskedArray.__getitem__(result, ())
        elif self.mask is not None:
            result = np.ma.MaskedArray.__getitem__(self.nxdata, idx)
        else:
            result = np.asarray(self.nxdata[idx])
        return NXfield(result, name=self.nxname, attrs=self.safe_attrs)

    def __setitem__(self, idx, value):
        """Assign values to a NXfield slice.
        
        Parameters
        ----------
        idx : slice
            Slice to be modified.
        value
            Value to be added. The value must be compatible with the NXfield
            dtype and it must be possible to broadcast it to the shape of the 
            specified slice.
        """
        if self.nxfilemode == 'r':
            raise NeXusError("NeXus file opened as readonly")
        elif self.is_linked():
            raise NeXusError("Cannot modify an item in a linked group")
        elif self.dtype is None:
            raise NeXusError("Set the field dtype before assignment")
        if is_real_slice(idx):
            idx = convert_index(idx, self)
        if value is np.ma.masked:
            self._mask_data(idx)
        else:
            if isinstance(value, np.bool_) and self.dtype != np.bool_:
                raise NeXusError(
                    "Cannot set a Boolean value to a non-Boolean data type")
            elif value is np.ma.nomask:
                value = False
            if isinstance(value, NXfield):
                value = value.nxdata
            if self._value is not None:
                self._value[idx] = value
            if self.nxfilemode == 'rw':
                self._put_filedata(value, idx)
            elif self._value is None:
                if self.size > NX_MAXSIZE:
                    self._put_memdata(value, idx)
                else:
                    self._value = np.empty(self.shape, self.dtype)
                    if self.fillvalue:
                        self._value.fill(self.fillvalue)
                    elif is_string_dtype(self.dtype):
                        self._value.fill(' ')
                    else:
                        self._value.fill(0)
                    self._value[idx] = value
        self.set_changed()

    def _str_name(self, indent=0):
        s = text(self).replace('\r\n', '\n')
        if self.dtype is not None:
            if is_string_dtype(self.dtype):
                if len(s) > 60:
                    s = s[:56] + '...'
                try:
                    s = s[:s.index('\n')]+'...'
                except ValueError:
                    pass
                if self.size == 1:
                    s = "'" + s + "'"
            elif len(self) > 3 or '\n' in s or s == "":
                if self.shape is None:
                    dims = ''
                else:
                    dims = 'x'.join([text(n) for n in self.shape])
                s = "%s(%s)" % (self.dtype, dims)
        elif s == "":
            s = "None"
        try:
            return " " * indent + self.nxname + " = " + s
        except Exception:
            return " " * indent + self.nxname

    def _get_filedata(self, idx=()):
        """Return the specified slab from the NeXus file.
        
        Parameters
        ----------
        idx : slice, optional
            Slice indices, by default ().
        
        Returns
        -------
        array_like
            Array containing the slice values.
        """
        with self.nxfile as f:
            result = f.readvalue(self.nxfilepath, idx=idx)
            if 'mask' in self.attrs:
                try:
                    mask = self.nxgroup[self.attrs['mask']]
                    result = np.ma.array(result, 
                                         mask=f.readvalue(mask.nxfilepath,
                                                          idx=idx))
                except KeyError:
                    pass
        return result

    def _put_filedata(self, value, idx=()):
        """Write the specified slice to the NeXus file.
        
        Parameters
        ----------
        value
            Slice values to be written.
        idx : slice, optional
            Slice indices, by default ().
        """
        with self.nxfile as f:
            if isinstance(value, np.ma.MaskedArray):
                if self.mask is None:
                    self._create_mask()
                f.writevalue(self.nxpath, value.data, idx=idx)
                f.writevalue(self.mask.nxpath, value.mask, idx=idx)
            else:
                f.writevalue(self.nxpath, value, idx=idx)

    def _get_memdata(self, idx=()):
        """Retrieve data from HDF5 core memory file.
        
        Parameters
        ----------
        idx : slice, optional
            Slice indices, by default ().
        
        Returns
        -------
        array_like
            Array containing the slice values.
        """
        result = self._memfile['data'][idx]
        if 'mask' in self._memfile:
            mask = self._memfile['mask'][idx]
            if mask.any():
                result = np.ma.array(result, mask=mask)
        return result
    
    def _put_memdata(self, value, idx=()):
        """Write the specified slice to HDF5 core memory file.
        
        Parameters
        ----------
        value
            Slice values to be written.
        idx : slice, optional
            Slice indices, by default ().
        """
        if self._memfile is None:
            self._create_memfile()
        if 'data' not in self._memfile:
            self._create_memdata()
        self._memfile['data'][idx] = value
        if isinstance(value, np.ma.MaskedArray):
            if 'mask' not in self._memfile:
                self._create_memmask()
            self._memfile['mask'][idx] = value.mask
    
    def _create_memfile(self):
        """Create an HDF5 core memory file to store the data."""
        import tempfile
        self._memfile = h5.File(tempfile.mkstemp(suffix='.nxs')[1], mode='r+',
                                driver='core', backing_store=False).file

    def _create_memdata(self):
        """Create an HDF5 core memory dataset to store the data."""
        if self._shape is not None and self._dtype is not None:
            if self._memfile is None:
                self._create_memfile()
            self._memfile.create_dataset('data', shape=self._shape, 
                                         dtype=self._dtype, **self._h5opts)
        else:
            raise NeXusError(
                "Cannot allocate to field before setting shape and dtype")       

    def _create_memmask(self):
        """Create an HDF5 core memory dataset to store the data mask."""
        if self._shape is not None:
            if self._memfile is None:
                self._create_memfile()
            self._memfile.create_dataset('mask', shape=self._shape, 
                                         dtype=np.bool, **self._h5opts)
        else:
            raise NeXusError("Cannot allocate mask before setting shape")       

    def _create_mask(self):
        """Create a data mask field if none exists."""
        if self.nxgroup is not None:
            if 'mask' in self.attrs:
                mask_name = self.attrs['mask']
                if mask_name in self.nxgroup:
                    return mask_name
            mask_name = '%s_mask' % self.nxname
            self.nxgroup[mask_name] = NXfield(shape=self._shape, dtype=np.bool, 
                                              fillvalue=False)
            self.attrs['mask'] = mask_name
            return mask_name
        return None      

    def _mask_data(self, idx=()):
        """Add a data mask covering the specified indices.
        
        Parameters
        ----------
        idx : slice, optional
            Slice indices, by default ().
        
        """
        mask_name = self._create_mask()
        if mask_name:
            self.nxgroup[mask_name][idx] = True
        elif self._memfile:
            if 'mask' not in self._memfile:
                self._create_memmask()
            self._memfile['mask'][idx] = True
        if self._value is not None:
            if not isinstance(self._value, np.ma.MaskedArray):
                self._value = np.ma.array(self._value)
            self._value[idx] = np.ma.masked

    def _get_uncopied_data(self, idx=None):
        """Retrieve copied data from a NeXus file.

        The HDF5 copy command is used to copy the data directly to a 
        new file. If no file is opened, it is copied to a core 
        memory file.

        Parameters
        ----------
        idx : slice, optional
            Slice indices, by default None.
        
        Returns
        -------
        array_like
            Array containing the copied values.
        """
        _file, _path = self._uncopied_data
        with _file as f:
            if idx:
                return f.readvalue(_path, idx=idx)
            else:
                if self.nxfilemode == 'rw':
                    f.copy(_path, self.nxpath)
                else:
                    self._create_memfile()
                    f.copy(_path, self._memfile, name='data')
                self._uncopied_data = None
                if (np.prod(self.shape) * np.dtype(self.dtype).itemsize 
                    <= NX_MEMORY*1000*1000):
                    return f.readvalue(_path)
                else:
                    return None

    def __deepcopy__(self, memo={}):
        """Return a deep copy of the field and its attributes."""
        obj = self
        dpcpy = obj.__class__()
        memo[id(self)] = dpcpy
        dpcpy._name = copy(self.nxname)
        dpcpy._dtype = copy(obj.dtype)
        dpcpy._shape = copy(obj.shape)
        dpcpy._h5opts = copy(obj._h5opts)
        dpcpy._changed = True
        dpcpy._memfile = obj._memfile
        dpcpy._uncopied_data = obj._uncopied_data
        if obj._value is not None:
            dpcpy._value = copy(obj._value)
            dpcpy._memfile = dpcpy._uncopied_data = None
        elif obj.nxfilemode:
            dpcpy._uncopied_data = (obj.nxfile, obj.nxpath)
        for k, v in obj.attrs.items():
            dpcpy.attrs[k] = copy(v)
        if 'target' in dpcpy.attrs:
            del dpcpy.attrs['target']
        dpcpy._group = None
        return dpcpy

    def __iter__(self):
        """Implement key iteration."""
        try:
            return self.nxvalue.__iter__()
        except AttributeError:
            return self
            
    def __next__(self):
        """Implements key iteration."""
        try:
            return self.nxvalue.__next__()
        except AttributeError:
            raise StopIteration
            
    def __contains__(self, key):
        """Implement 'k in d' test using the NXfield `nxvalue`."""
        return self.nxvalue.__contains__(key)

    def __len__(self):
        """Return the length of the NXfield data."""
        try:
            return self.shape[0]
        except Exception:
            return 0

    def any(self):
        """Return False if all values are 0 or False, True otherwise."""
        try:
            return np.any(self.nxvalue)
        except TypeError as error:
            raise NeXusError("Invalid field type for numeric comparisons")

    def all(self):
        """Return False if any values are 0 or False, True otherwise."""
        try:
            return np.all(self.nxvalue)
        except TypeError as error:
            raise NeXusError("Invalid field type for numeric comparisons")

    def index(self, value, max=False):
        """Return the index of a value in a one-dimensional NXfield.

        The index is less than (greater than) or equal to the given value for 
        a monotonically increasing (decreasing) array.

        Parameters
        ----------
        value : int or float
            Value to be indexed.
        max : bool, optional
            True if the index is greater than (less than) or equal to the 
            value for a monotonically increasing (decreasing) array, 
            by default False.
        
        Returns
        -------
        int
            Index of value.

        Examples
        --------
        
        >>> field
        NXfield([ 0.   0.1  0.2 ...,  0.8  0.9  1. ])
        >>> field.index(0.1)
        1
        >>> field.index(0.11)
        1
        >>> field.index(0.11, max=True)
        2
        >>> reverse_field
        NXfield([ 1.   0.9  0.8 ...,  0.2  0.1  0. ])
        >>> reverse_field.index(0.89)
        1
        >>> reverse_field.index(0.89, max=True)
        2

        The value is considered to be equal to an NXfield element's value if it
        differs by less than 1% of the step size to the neighboring element. 
        """
        if self.ndim != 1:
            raise NeXusError(
                "NXfield must be one-dimensional to use the index function")
        if self.nxdata[-1] < self.nxdata[0]:
            flipped = True
        else:
            flipped = False
        if max:
            if flipped:
                idx = np.max(len(self.nxdata) - 
                             len(self.nxdata[self.nxdata<value])-1,0)
            else:
                idx = np.max(len(self.nxdata) - 
                             len(self.nxdata[self.nxdata>value])-1,0)
            try:
                diff = value - self.nxdata[idx]
                step = self.nxdata[idx+1] - self.nxdata[idx]
                if abs(diff/step) > 0.01:
                    idx = idx + 1
            except IndexError:
                pass
        else:
            if flipped:
                idx = len(self.nxdata[self.nxdata>value])
            else:
                idx = len(self.nxdata[self.nxdata<value])
            try:
                diff = value - self.nxdata[idx-1]
                step = self.nxdata[idx] - self.nxdata[idx-1]
                if abs(diff/step) < 0.99:
                    idx = idx - 1
            except IndexError:
                pass
        return int(np.clip(idx, 0, len(self.nxdata)-1))

    def __array__(self):
        """Cast the NXfield as a Numpy array."""
        return np.asarray(self.nxdata)

    def __array_wrap__(self, value):
        """Transform the array resulting from a ufunc to an NXfield."""
        return NXfield(value, name=self.nxname)

    def __int__(self):
        """Cast a scalar field as an integer."""
        return int(self.nxvalue)

    def __long__(self):
        """Cast a scalar field as a long integer.

        The use of the `long` function is not valid in Python 3 and 
        no longer useful in Python 2.
        """
        return int(self.nxvalue)

    def __float__(self):
        """Cast a scalar field as floating point number."""
        return float(self.nxvalue)

    def __complex__(self):
        """Cast a scalar field as a complex number."""
        return complex(self.nxvalue)

    def __neg__(self):
        """Return the negative value of a scalar field."""
        return -self.nxvalue

    def __abs__(self):
        """Return the absolute value of a scalar field."""
        return abs(self.nxvalue)

    def __eq__(self, other):
        """Return true if the values of another NXfield are the same."""
        if id(self) == id(other):
            return True
        elif isinstance(other, NXfield):
            if (isinstance(self.nxvalue, np.ndarray) and
                   isinstance(other.nxvalue, np.ndarray)):
                try:
                    return np.array_equal(self, other)
                except ValueError:
                    return False
            else:
                return self.nxvalue == other.nxvalue
        else:
            return self.nxvalue == other

    def __ne__(self, other):
        """Return true if the values of another NXfield are not the same."""
        if isinstance(other, NXfield):
            if (isinstance(self.nxvalue, np.ndarray) and
                   isinstance(other.nxvalue, np.ndarray)):
                try:
                    return not np.array_equal(self, other)
                except ValueError:
                    return True
            else:
                return self.nxvalue != other.nxvalue
        else:
            return self.nxvalue != other

    def __lt__(self, other):
        """Return true if self.nxvalue < other[.nxvalue]."""
        if isinstance(other, NXfield):
            return self.nxvalue < other.nxvalue
        else:
            return self.nxvalue < other

    def __le__(self, other):
        """Return true if self.nxvalue <= other[.nxvalue]."""
        if isinstance(other, NXfield):
            return self.nxvalue <= other.nxvalue
        else:
            return self.nxvalue <= other

    def __gt__(self, other):
        """Return true if self.nxvalue > other[.nxvalue]."""
        if isinstance(other, NXfield):
            return self.nxvalue > other.nxvalue
        else:
            return self.nxvalue > other

    def __ge__(self, other):
        """Return true if self.nxvalue >= other[.nxvalue]."""
        if isinstance(other, NXfield):
            return self.nxvalue >= other.nxvalue
        else:
            return self.nxvalue >= other

    def __add__(self, other):
        """Return the sum of the NXfield and another NXfield or number."""
        if isinstance(other, NXfield):
            return NXfield(value=self.nxdata+other.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=self.nxdata+other, name=self.nxname,
                           attrs=self.safe_attrs)
 
    def __radd__(self, other):
        """Return the sum of the NXfield and a NXfield or number.

        This variant makes __add__ commutative.
        """
        return self.__add__(other)

    def __sub__(self, other):
        """Return the NXfield subtracting a NXfield or number."""
        if isinstance(other, NXfield):
            return NXfield(value=self.nxdata-other.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=self.nxdata-other, name=self.nxname,
                           attrs=self.safe_attrs)

    def __rsub__(self, other):
        """Returns the NXfield after subtracting a NXfield or number."""
        if isinstance(other, NXfield):
            return NXfield(value=other.nxdata-self.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=other-self.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)

    def __mul__(self, other):
        """Return the product of the NXfield and another NXfield or number."""
        if isinstance(other, NXfield):
            return NXfield(value=self.nxdata*other.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=self.nxdata*other, name=self.nxname,
                           attrs=self.safe_attrs)

    def __rmul__(self, other):
        """Return the product of the NXfield and another NXfield or number.

        This variant makes __mul__ commutative.
        """
        return self.__mul__(other)

    def __truediv__(self, other):
        """Returns the NXfield divided by another NXfield or number."""
        if isinstance(other, NXfield):
            return NXfield(value=self.nxdata/other.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=self.nxdata/other, name=self.nxname,
                           attrs=self.safe_attrs)

    __div__ = __truediv__

    def __rtruediv__(self, other):
        """Return the inverse of the NXfield divided by a NXfield or number."""
        if isinstance(other, NXfield):
            return NXfield(value=other.nxdata/self.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)
        else:
            return NXfield(value=other/self.nxdata, name=self.nxname,
                           attrs=self.safe_attrs)

    __rdiv__ = __rtruediv__

    def __pow__(self, power):
        """Return the NXfield raised to the specified power."""
        return NXfield(value=pow(self.nxdata,power), name=self.nxname,
                       attrs=self.safe_attrs)

    def min(self, axis=None):
        """Return the minimum value of the array ignoring NaNs."""
        return np.nanmin(self.nxdata[self.nxdata>-np.inf], axis) 

    def max(self, axis=None):
        """Return the maximum value of the array ignoring NaNs."""
        return np.nanmax(self.nxdata[self.nxdata<np.inf], axis) 

    def sum(self, axis=None):
        """Return the sum of NXfield values.
        
        Parameters
        ----------
        axis : int or tuple of ints, optional
            Axis or axes to be summed over, by default all axes.
        
        Returns
        -------
        NXfield
            Summed values.
        """
        return NXfield(np.sum(self.nxdata, axis), name=self.nxname, 
                       attrs=self.safe_attrs)

    def average(self, axis=None):
        """Return the average of NXfield values.
        
        Parameters
        ----------
        axis : int or tuple of ints, optional
            Axis or axes to be averaged, by default all axes.
        
        Returns
        -------
        NXfield
            Averaged values.
        """
        return NXfield(np.average(self.nxdata, axis), name=self.nxname, 
                       attrs=self.safe_attrs)

    def reshape(self, shape):
        """Return an NXfield with the specified shape."""
        return NXfield(value=self.nxdata, name=self.nxname, shape=shape,
                       attrs=self.safe_attrs)

    def transpose(self):
        """Return an NXfield containing the transpose of the data array."""
        value = self.nxdata.transpose()
        return NXfield(value=value, name=self.nxname,
                       shape=value.shape, attrs=self.safe_attrs)

    @property
    def T(self):
        return self.transpose()

    def centers(self):
        """Return a NXfield with bin centers.

        This is used for one-dimensional fields containing axes that are
        stored as bin boundaries.
        """
        return NXfield((self.nxdata[:-1]+self.nxdata[1:])/2,
                        name=self.nxname, attrs=self.safe_attrs)

    def boundaries(self):
        """Return a NXfield with bin boundaries.

        This is used for one-dimensional fields containing axes that are
        stored as bin centers.
        """
        ax = self.nxdata
        start = ax[0] - (ax[1] - ax[0])/2
        end = ax[-1] + (ax[-1] - ax[-2])/2
        return NXfield(np.concatenate((np.atleast_1d(start), 
                                       (ax[:-1] + ax[1:])/2, 
                                       np.atleast_1d(end))),
                       name=self.nxname, attrs=self.safe_attrs)

    def add(self, data, offset):
        """Add a slab into the data array.
        
        Parameters
        ----------
        data : array_like
            Slab values to be added to the field.
        offset : tuple
            Offsets containing the lowest slab indices.
        """
        idx = tuple(slice(i,i+j) for i,j in zip(offset,data.shape))
        if isinstance(data, NXfield):
            self[idx] += data.nxdata.astype(self.dtype)
        else:
            self[idx] += data.astype(self.dtype)

    def convert(self, units=""):
        """Returns the data in the requested units.
        
        This is not currently implemented.
        """
        try:
            import units
        except ImportError:
            raise NeXusError("No conversion utility available")
        if self._value is not None:
            return self._converter(self.nxvalue, units)
        else:
            return None

    def walk(self):
        yield self

    def replace(self, value):
        """Replace the value of a field.

        If the size or dtype of the field differs from an existing field within
        a saved group, the original field will be deleted and replaced by the 
        newone. Otherwise, the field values are updated.
        """
        group = self.nxgroup
        if group is None:
            raise NeXusError("The field must be a member of a group")
        if isinstance(value, NXfield):
            del group[self.nxname]
            group[self.nxname] = value
        elif is_text(value):
            if self.dtype == string_dtype:
                self.nxdata = value
                group.update()
            else:
                del group[self.nxname]
                group[self.nxname] = NXfield(value, attrs=self.attrs)
        else:
            value = np.asarray(value)
            if value.shape == self.shape and value.dtype == self.dtype:
                self.nxdata = value
                group.update()
            else:
                del group[self.nxname]
                group[self.nxname] = NXfield(value, attrs=self.attrs)

    @property
    def nxaxes(self):
        """List of NXfields containing axes.

        If the NXfield does not have the 'axes' attribute but is defined as
        the signal in its parent group, a list of the parent group's axes will
        be returned. 
        """
        def invalid_axis(axis):
            return axis.size != self.shape[i] and axis.size != self.shape[i]+1
        def empty_axis(i):
            return NXfield(np.arange(self.shape[i]), name='Axis%s'%i)
        def plot_axis(axis):
            return NXfield(axis.nxvalue, name=axis.nxname, attrs=axis.attrs) 
        if self.nxgroup:
            if 'axes' in self.attrs:
                axis_names = _readaxes(self.attrs['axes'])
            elif 'axes' in self.nxgroup.attrs:
                axis_names = _readaxes(self.nxgroup.attrs['axes'])
            else:
                axis_names = ['.'] * self.plot_rank
            if len(axis_names) > self.plot_rank:
                axis_names = axis_names[:self.plot_rank]
            axes = []
            for i, axis_name in enumerate(axis_names):
                axis_name = axis_name.strip()
                if (axis_name not in self.nxgroup or  
                    invalid_axis(self.nxgroup[axis_name])):
                    axes.append(empty_axis(i))
                else:
                    axes.append(plot_axis(self.nxgroup[axis_name]))
            return axes
        else:
            return [empty_axis(i) for i in range(self.plot_rank)]

    def valid_axes(self, axes):
        """Return True if the axes are consistent with the field.
        
        It checks that all the axes are one-dimensional, and that the size of
        each axis is equal to or one greater than the field dimension.
        
        Parameters
        ----------
        axes : list
            List of NXfields
        
        Notes
        -----
        The function removes scalar axes before the check even though these are 
        returned by the nxaxes property. That is because ndim is 0 for scalars.
        They are automatically removed when plotting so this does not 
        invalidate the check.
        """
        if not is_iterable(axes):
            axes = [axes]
        plot_axes = [axis for axis in axes if axis.size > 1]
        axis_shape = [axis.size for axis in plot_axes]
        if (all(axis.ndim == 1 for axis in plot_axes) and 
            len([x for x,y in zip(self.plot_shape, axis_shape) 
                 if x==y or x==y-1]) == self.plot_rank):
            return True
        else:
            return False

    @property
    def nxvalue(self):
        """NXfield value.
        
        This is the value stored in the NeXus file, with the following
        exceptions.
            1) Size-1 arrays are returned as scalars.
            2) String or byte arrays are returns as a list of strings.

        Notes
        -----
        If unmodified values are required, use the `nxdata` property.
        """
        _value = self.nxdata
        if _value is None:
            return None
        elif (self.dtype is not None and
            (self.dtype.type == np.string_ or self.dtype.type == np.str_ or 
             self.dtype == string_dtype)):
            if self.shape == ():
                return text(_value)
            elif self.shape == (1,):
                return text(_value[0])
            else:
                return [text(value) for value in _value[()]]
        elif self.shape == (1,):
            return _value.item()
        else:
            return _value

    @property
    def nxdata(self):
        """NXfield data as stored in a file.
        
        If the requested data is larger than NX_MEMORY,the return value 
        is `None`.
        """
        if self._value is None:
            if self.dtype is None or self.shape is None:
                return None
            if (np.prod(self.shape) * np.dtype(self.dtype).itemsize 
                <= NX_MEMORY*1000*1000):
                try:
                    if self.nxfilemode:
                        self._value = self._get_filedata()
                    elif self._uncopied_data:
                        self._value = self._get_uncopied_data()
                    if self._memfile:
                        self._value = self._get_memdata()
                except Exception:
                    raise NeXusError("Cannot read data for '%s'" % self.nxname)
                if self._value is not None:
                    self._value.shape = self.shape
            else:
                raise NeXusError(
                    "Use slabs to access data larger than NX_MEMORY=%s MB" 
                    % NX_MEMORY)
        if self.mask is not None:
            try:
                if isinstance(self.mask, NXfield):
                    mask = self.mask.nxdata
                    if isinstance(self._value, np.ma.MaskedArray):
                        self._value.mask = mask
                    else:
                        self._value = np.ma.array(self._value, mask=mask)
            except Exception:
                pass
        return self._value

    @nxdata.setter
    def nxdata(self, value):
        if self.nxfilemode == 'r':
            raise NeXusError("NeXus file is locked")
        else:
            self._value, self._dtype, self._shape = _getvalue(
                value, self._dtype, self._shape)
            if self._memfile:
                self._put_memdata(self._value)

    @property
    def nxtitle(self):
        """Title as a string.

        If there is no title attribute in the parent group, the group's path is 
        returned.
        """
        root = self.nxroot
        if root.nxname != '' and root.nxname != 'root':
            return (root.nxname + '/' + self.nxpath.lstrip('/')).rstrip('/')
        else:
            fname = self.nxfilename
            if fname is not None:
                return fname + ':' + self.nxpath
            else:
                return self.nxpath

    @property
    def mask(self):
        """NXfield's mask as an array.

        Only works if the NXfield is in a group and has the 'mask' attribute set
        or if the NXfield array is defined as a masked array.
        """
        if 'mask' in self.attrs:
            if self.nxgroup and self.attrs['mask'] in self.nxgroup:
                return self.nxgroup[self.attrs['mask']]
        if self._value is None and self._memfile:
            if 'mask' in self._memfile:
                return self._memfile['mask']      
        if self._value is not None and isinstance(self._value, 
                                                  np.ma.MaskedArray):
            return self._value.mask
        return None

    @mask.setter
    def mask(self, value):
        if self.nxfilemode == 'r':
            raise NeXusError("NeXus file opened as readonly")
        elif self.is_linked():
            raise NeXusError("Cannot modify an item in a linked group")
        if 'mask' in self.attrs:
            if self.nxgroup:
                mask_name = self.attrs['mask']
                if mask_name in self.nxgroup:
                    self.nxgroup[mask_name][()] = value
            else:
                del self.attrs['mask']
        elif self._value is None:
            if self._memfile:
                if 'mask' not in self._memfile:
                    self._create_memmask()
                self._memfile['mask'][()] = value
        if self._value is not None:
            if isinstance(self._value, np.ma.MaskedArray):
                self._value.mask = value
            else:
                self._value = np.ma.array(self._value, mask=value)

    def resize(self, shape, axis=None):
        """Resize the NXfield.
        
        Parameters
        ----------
        shape : tuple of ints
            Requested shape.
        axis : int, optional
            Axis whose length is to be resized, by default None
        """
        if axis is not None:
            if not (axis >=0 and axis < self.ndim):
                raise NeXusError("Invalid axis (0 to %s allowed)" 
                                 % (self.ndim-1))
            try:
                newlen = int(shape)
            except TypeError:
                raise NeXusError(
                    "Argument must be a single integer if axis is specified")
            shape = list(self._shape)
            shape[axis] = newlen
        if self.checkshape(shape):
            if self.nxfilemode:
                with self.nxfile as f:
                    f[self.nxpath].shape = shape
                self._value = None
            elif self._memfile:
                self._memfile['data'].shape = shape
                self._value = None
        else:
            raise NeXusError("Shape incompatible with current NXfield")
        self._shape = shape
        if self._value is not None:
            self._value.resize(self._shape, refcheck=False)

    def checkshape(self, shape):
        """Return True if the shape argument is compatible with the NXfield."""
        _maxshape = self.maxshape
        if _maxshape and not _checkshape(shape, _maxshape):
            return False
        elif self.nxfilemode or self._memfile:
            return _checkshape(self._shape, shape)
        else:
            return True

    @property
    def shape(self):
        """Shape of the NXfield."""
        try:
            return _getshape(self._shape)
        except TypeError:
            return ()

    @shape.setter
    def shape(self, value):
        self.resize(value)

    @property
    def dtype(self):
        """Dtype of the NXfield."""
        return self._dtype

    @dtype.setter
    def dtype(self, value):
        if self.nxfilemode:
            raise NeXusError(
                "Cannot change the dtype of a field already stored in a file")
        elif self._memfile:
            raise NeXusError(
                "Cannot change the dtype of a field already in core memory")
        self._dtype = _getdtype(value)
        if self._value is not None:
            self._value = np.asarray(self._value, dtype=self._dtype)

    def get_h5opt(self, name):
        """Return the option set for the h5py dataset.
        
        Parameters
        ----------
        name : str
            Name of the h5py option.
        """
        if self.nxfilemode:
            with self.nxfile as f:
                self._h5opts[name] = getattr(f[self.nxfilepath], name)
        elif self._memfile:
            self._h5opts[name] = getattr(self._memfile['data'], name)
        if name in self._h5opts:
            return self._h5opts[name]
        else:
            return None

    def set_h5opt(self, name, value):
        """Set the value of a h5py option.
        
        Parameters
        ----------
        name : str
            Name of option.
        value
            Option value.
        """
        if self.nxfilemode:
            raise NeXusError(
            "Cannot change the %s of a field already stored in a file" % name)
        elif self._memfile:
            raise NeXusError(
            "Cannot change the %s of a field already in core memory" % name)
        if value is not None:
            self._h5opts[name] = value
        
    @property
    def compression(self):
        """NXfield compression."""
        return self.get_h5opt('compression')

    @compression.setter
    def compression(self, value):
        self.set_h5opt('compression', value)
        
    @property
    def compression_opts(self):
        """NXfield compression options."""
        return self.get_h5opt('compression_opts')

    @compression_opts.setter
    def compression_opts(self, value):
        self.set_h5opt('compression_opts', value)
        
    @property
    def fillvalue(self):
        """NXfield fill value."""
        return self.get_h5opt('fillvalue')

    @fillvalue.setter
    def fillvalue(self, value):
        self.set_h5opt('fillvalue', value)

    @property
    def fletcher32(self):
        """True if Fletcher32 checksum used."""
        return self.get_h5opt('fletcher32')

    @fletcher32.setter
    def fletcher32(self, value):
        self.set_h5opt('fletcher32', value)
        
    @property
    def chunks(self):
        """NXfield chunk size."""
        return self.get_h5opt('chunks')

    @chunks.setter
    def chunks(self, value):
        if is_iterable(value) and len(value) != self.ndim:
            raise NeXusError(
                "Number of chunks does not match the no. of array dimensions")
        self.set_h5opt('chunks', value)

    @property
    def maxshape(self):
        """NXfield maximum shape."""
        return self.get_h5opt('maxshape')

    @maxshape.setter
    def maxshape(self, value):
        self.set_h5opt('maxshape', _getmaxshape(value, self.shape))

    @property
    def scaleoffset(self):
        """NXfield scale offset."""
        return self.get_h5opt('scaleoffset')

    @scaleoffset.setter
    def scaleoffset(self, value):
        self.set_h5opt('scaleoffset', value)
        
    @property
    def shuffle(self):
        """True if the shuffle filter enabled."""
        return self.get_h5opt('shuffle')

    @shuffle.setter
    def shuffle(self, value):
        self.set_h5opt('shuffle', value)
        
    @property
    def ndim(self):
        """Rank of the NXfield."""
        try:
            return len(self.shape)
        except TypeError:
            return 0

    @property
    def size(self):
        """Total size of the NXfield."""
        return int(np.prod(self.shape))

    @property
    def safe_attrs(self):
        """Attributes that can be safely copied to derived NXfields."""
        return {key: self.attrs[key] for key in self.attrs 
                if (key != 'target' and key != 'signal' and key != 'axes')}

    @property
    def reversed(self):
        """True if the one-dimensional field has decreasing values."""
        if self.ndim == 1 and self.nxdata[-1] < self.nxdata[0]:
            return True
        else:
            return False

    @property
    def plot_shape(self):
        """Shape of NXfield for plotting.
        
        Size-1 axes are removed from the shape.
        """
        try:  
            _shape = list(self.shape)
            while 1 in _shape:
                _shape.remove(1)
            return tuple(_shape)
        except Exception:
            return ()

    @property
    def plot_rank(self):
        """Rank of the NXfield when plotting."""
        return len(self.plot_shape)

    def is_numeric(self):
        """True if the NXfield contains numeric data."""
        return not is_string_dtype(self.dtype)

    def is_string(self):
        """True if the NXfield contains strings."""
        return is_string_dtype(self.dtype)

    def is_plottable(self):
        """True if the NXfield is plottable."""
        if self.plot_rank > 0:
            return True
        else:
            return False

    def is_image(self):
        """True if the field is compatible with an RGB(A) image."""
        return self.ndim == 3 and (self.shape[2] == 3 or self.shape[2] == 4) 

    def plot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
             vmin=None, vmax=None, **kwargs):
        """Plot the NXfield.
        
        The format argument is used to set the color and type of the
        markers or lines for one-dimensional plots, using the standard 
        Matplotlib syntax. The default is set to blue circles. All 
        keyword arguments accepted by matplotlib.pyplot.plot can be
        used to customize the plot.
        
        Parameters
        ----------
        fmt : str, optional
            Matplotlib format string, by default ''
        xmin : float, optional
            Minimum x-value in plot, by default None
        xmax : float, optional
            Maximum x-value in plot, by default None
        ymin : float, optional
            Minimum y-value in plot, by default None
        ymax : float, optional
            Maximum y-value in plot, by default None
        vmin : float, optional
            Minimum signal value for 2D plots, by default None
        vmax : float, optional
            Maximum signal value for 2D plots, by default None

        Notes
        -----
        In addition to the Matplotlib keyword arguments, the following
        are defined ::
        
            log = True     - plot the intensity on a log scale
            logy = True    - plot the y-axis on a log scale
            logx = True    - plot the x-axis on a log scale
            over = True    - plot on the current figure
            image = True   - plot as an RGB(A) image
        """
        if not self.exists():
            raise NeXusError("'%s' does not exist"
                             % os.path.abspath(self.nxfilename))

        try:
            from __main__ import plotview
            if plotview is None:
                raise ImportError
        except ImportError:
            from .plot import plotview

        if self.is_plottable():
            data = NXdata(self, self.nxaxes, title=self.nxtitle)
            if self.nxroot.nxclass == "NXroot":
                signal_path = self.nxroot.nxname + self.nxpath
            else:
                signal_path = self.nxpath
            data.nxsignal.attrs['signal_path'] = signal_path
            plotview.plot(data, fmt, xmin=None, xmax=None, ymin=None, ymax=None,
                          vmin=None, vmax=None, **kwargs)
        else:
            raise NeXusError("NXfield not plottable")
    
    def oplot(self, fmt='', **kwargs):
        """Plot the NXfield over the current figure."""
        self.plot(fmt=fmt, over=True, **kwargs)

    def logplot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
                vmin=None, vmax=None, **kwargs):
        """Plot the NXfield on a log scale."""
        self.plot(fmt=fmt, log=True,
                  xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                  vmin=vmin, vmax=vmax, **kwargs)

    def implot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
                vmin=None, vmax=None, **kwargs):
        """Plots the NXfield as an RGB(A) image."""
        if self.plot_rank > 2 and (self.shape[-1] == 3 or self.shape[-1] == 4):
            self.plot(fmt=fmt, image=True,
                      xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                      vmin=vmin, vmax=vmax, **kwargs)
        else:
            raise NeXusError("Invalid shape for RGB(A) image")


SDS = NXfield # For backward compatibility


class NXgroup(NXobject):

    """NeXus group.

    This is a subclass of NXobject and is the base class for the specific
    NeXus group classes, *e.g.*, NXentry, NXsample, NXdata.

    Parameters
    ----------
        name : str
            The name of the NXgroup. If the NXgroup is initialized as the 
            attribute of a parent group, the name is automatically set to 
            the name of this attribute. If 'nxclass' is specified and has 
            the usual prefix 'NX', the default name is the class name 
            without this prefix.
        nxclass : str
            The class of the NXgroup.
        entries : dict
            A dictionary containing a list of group entries. This is an
            alternative way of adding group entries to the use of keyword
            arguments.
        group : NXgroup
            The parent NeXus group, which is accessible as the group attribute
            'group'. If the group is initialized as the attribute of
            a parent group, this is set to the parent group.
        args : NXfield or NXgroup
            Positional arguments must be valid NeXus objects, either an 
            NXfield or a NeXus group. These are added without modification 
            as children of this group.
        kwargs : dict
            Keyword arguments are used to add children to the group. The keyword 
            values must be valid NeXus objects, either NXfields or NXgroups. 
            The keys are used to set the names within the group.

    Attributes
    ----------
    nxclass : str
        The class of the NXgroup.
    nxname : str
        The name of the NXfield.
    entries : dict
        A dictionary of all the NeXus objects contained within an NXgroup.
    attrs : AttrDict
        A dictionary of all the NeXus attributes, *i.e.*, attribute with class 
        NXattr.
    nxpath : str
        The path to this object with respect to the root of the NeXus tree. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.
    nxroot : NXgroup
        The root object of the NeXus tree containing this object. For
        NeXus data read from a file, this will be a group of class NXroot, but
        if the NeXus tree was defined interactively, it can be any valid
        NXgroup.

    Examples
    --------
    Just as in a NeXus file, NeXus groups can contain either data or other
    groups, represented by NXfield and NXgroup objects respectively. To
    distinguish them from regular Python attributes, all NeXus objects are
    stored in the 'entries' dictionary of the NXgroup. However, they can usually
    be assigned or referenced as if they are Python attributes, *i.e.*, using 
    the dictionary name directly as the group attribute name, as long as this 
    name is not the same as one of the Python attributes defined above or as one 
    of the NXfield Python attributes.

    1) Assigning a NeXus object to a NeXus group

        In the example below, after assigning the NXgroup, the following three
        NeXus object assignments to entry.sample are all equivalent:

        >>> entry.sample = NXsample()
        >>> entry.sample['temperature'] = NXfield(40.0)
        >>> entry['sample/temperature'] = NXfield(40.0)
        >>> entry.sample.temperature = 40.0
        >>> entry.sample.temperature
        NXfield(40.0)

        If the assigned value is not a valid NXobject, then it is cast as an NXfield
        with a type determined from the Python data type.

        >>> entry.sample.temperature = 40.0
        >>> entry.sample.temperature
        NXfield(40.0)
        >>> entry.data.data.x=np.linspace(0,10,11).astype('float32')
        >>> entry.data.data.x
        NXfield([  0.   1.   2. ...,   8.   9.  10.])

    2) Referencing a NeXus object in a NeXus group

        If the name of the NeXus object is not the same as any of the Python
        attributes listed above, or the methods listed below, they can be 
        referenced as if they were a Python attribute of the NXgroup. However, 
        it is only possible to reference attributes with one of the proscribed 
        names using the group dictionary, i.e.,

        >>> entry.sample.temperature = 100.0
        >>> print entry.sample.temperature
        sample:NXsample
          temperature = 100.0
        >>> entry.sample['temperature']
        NXfield(100.0)

        For this reason, it is recommended to use the group dictionary to 
        reference all group objects within Python scripts.

    Notes
    -----
    All NeXus attributes are stored in the 'attrs' dictionary of the NXgroup, 
    but can be referenced as if they are Python attributes as long as there is 
    no name clash.

        >>> entry.sample.temperature = 40.0
        >>> entry.sample.attrs['value'] = 10.0
        >>> print(entry.sample.value)
        sample:NXsample
          @value = 10.0
          temperature = 40.0
        >>> entry.sample.attrs['value']
        NXattr(10.0)

    Examples
    --------
        >>> x = NXfield(np.linspace(0,2*np.pi,101), units='degree')
        >>> entry = NXgroup(x, name='entry', nxclass='NXentry')
        >>> entry.sample = NXgroup(temperature=NXfield(40.0,units='K'),
                               nxclass='NXsample')
        >>> print entry.sample.tree
        sample:NXsample
          temperature = 40.0
            @units = K

    All the currently defined NeXus classes are defined as subclasses of the 
    NXgroup class. It is recommended that these are used directly, so that the 
    above examples become:

        >>> entry = NXentry(x)
        >>> entry['sample'] = NXsample(temperature=NXfield(40.0,units='K'))

    or

        >>> entry['sample/temperature'] = 40.0
        >>> entry['sample/temperature'].units='K'
    """
    _class = "NXgroup"

    def __init__(self, *args, **kwargs):
        self._entries = {}
        if "name" in kwargs:
            self._name = kwargs.pop("name")
        if "nxclass" in kwargs:
            self._class = kwargs.pop("nxclass")
        if "group" in kwargs:
            self._group = kwargs.pop("group")
        if "entries" in kwargs:
            for k,v in kwargs["entries"].items():
                self._entries[k] = deepcopy(v)
            del kwargs["entries"]
        if "attrs" in kwargs:
            self._attrs = AttrDict(self, attrs=kwargs["attrs"])
            del kwargs["attrs"]
        else:
            self._attrs = AttrDict(self)
        for k,v in kwargs.items():
            try:
                self[k] = v
            except AttributeError:
                raise NeXusError(
                    "Keyword arguments must be valid NXobjects")
        if self.nxclass.startswith("NX"):
            if self.nxname == "unknown" or self.nxname == "": 
                self._name = self.nxclass[2:]
            try: # If one exists, set the class to a valid NXgroup subclass
                self.__class__ = _getclass(self._class)
            except Exception:
                pass
        for arg in args:
            try:
                self[arg.nxname] = arg
            except AttributeError:
                raise NeXusError(
                    "Non-keyword arguments must be valid NXobjects")
        self.set_changed()

    def __dir__(self):
        return sorted([c for c in dir(super(self.__class__, self))
                       if not c.startswith('_')]+list(self)+list(self.attrs), 
                      key=natural_sort)

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.nxname)

    def __hash__(self):
        return id(self)

    def __getattr__(self, name):
        """Return attribute looking in the group entries and attributes.

        If the attribute is the name of a defined NeXus class, a list of group
        entries of that class are returned.
        """
        if name.startswith(u'NX'):
            return self.component(name)
        elif name in self.entries:
            return self.entries[name]
        elif name in self.attrs:
            return self.attrs[name]
        raise NeXusError("'"+name+"' not in "+self.nxpath)

    def __setattr__(self, name, value):
        """Set an attribute as an object or regular Python attribute.
        
        Parameters
        ----------
        name : str
            Name of the attribute
        value : NXfield or NXgroup or NXattr or str or array-like
            Value to be assigned to the attribute. If the value is a NXattr
            instance, it is assigned to the group `attrs` dictionary. 
            If the value is a NXfield or NXgroup, it is added to the group 
            entries with the assigned name. Otherwise, the value is converted
            to a NXfield. The parent group of the attribute is set to the 
            current group.

        Notes
        -----
        If the attribute name starts with 'nx' or '_', they are assigned as
        NXgroup attributes without further conversions.
        """
        if name.startswith('_') or name.startswith('nx'):
            object.__setattr__(self, name, value)
        elif isinstance(value, NXattr):
            if self.nxfilemode == 'r':
                raise NeXusError("NeXus file opened as readonly")
            elif self.is_linked():
                raise NeXusError("Cannot modify an item in a linked group")
            self._attrs[name] = value
        else:
            self[name] = value

    def __delattr__(self, name):
        """Delete an entry or attribute in the current group."""
        if name in self.entries or name in self.attrs:
            raise NeXusError(
                "Members can only be deleted using the group dictionary")
        else:
            object.__delattr__(self, name)

    def __getitem__(self, key):
        """Return a NeXus field or group in the current group."""
        if is_text(key):
            if '/' in key:
                if key.startswith('/'):
                    return self.nxroot[key[1:]]
                names = [name for name in key.split('/') if name]
                node = self
                for name in names:
                    if name in node:
                        node = node.entries[name]
                    else:
                        raise NeXusError("Invalid path")
                return node
            else:
                return self.entries[key]
        else:
            raise NeXusError("Invalid index")

    def __setitem__(self, key, value):
        """Add or modify entries to the group dictionary.
        
        All dictionary entries must be valid NeXus fields or groups. If the 
        value is a string or a Numpy array, a NeXus field of matching type is
        created. If the name refers to a NXfield that already exists in the 
        group, the field values are modified, provided that the new values are
        compatible with the field shape and dtype. 
        
        Parameters
        ----------
        key : str
            Name of the added entry.
        value : NXfield or NXgroup or str or array-like.
            Value to be added to the group.

        Notes
        -----
        If the key is a path within the NeXus tree, the value is added to the 
        base group in the path.
        """
        if is_text(key):
            group = self
            if '/' in key:
                names = [name for name in key.split('/') if name]
                key = names.pop()
                for name in names:
                    if name in group:
                        group = group[name]
                    else:
                        raise NeXusError("Invalid path")
            if group.nxfilemode == 'r':
                raise NeXusError("NeXus group marked as readonly")
            elif isinstance(group, NXlink):
                raise NeXusError("Cannot modify an item in a linked group")
            elif isinstance(value, NXroot):
                raise NeXusError(
                    "Cannot assign an NXroot group to another group")
            elif key in group and group.nxfilemode:
                if isinstance(value, NXgroup):
                    raise NeXusError(
                        "Cannot assign an NXgroup to an existing group entry")
                elif isinstance(value, NXlink):
                    raise NeXusError(
                        "Cannot assign an NXlink to an existing group entry")
                elif isinstance(group.entries[key], NXlink):
                    raise NeXusError("Cannot assign values to an NXlink")
                elif group.entries[key].is_linked():
                    raise NeXusError("Cannot modify an item in linked group")
                group.entries[key].nxdata = value
                if isinstance(value, NXfield):
                    group.entries[key]._setattrs(value.attrs)
            elif isinstance(value, NXobject):
                if group.nxfilemode is None and value._copyfile is not None:
                    raise NeXusError(
                        "Can only copy objects to another NeXus file.")
                if value._group:
                    value = deepcopy(value)
                value._group = group
                value._name = key
                if isinstance(value, NXlink):
                    value.initialize_link()
                group.entries[key] = value
            else:
                group.entries[key] = NXfield(value=value, name=key, group=group)
            if isinstance(group.entries[key], NXfield):
                field = group.entries[key]
                if not field._value is None:
                    if isinstance(field._value, np.ma.MaskedArray):
                        mask_name = field._create_mask()
                        group[mask_name] = field._value.mask
                elif field._memfile is not None:
                    if 'mask' in field._memfile:
                        mask_name = field._create_mask()
                        group[mask_name]._create_memfile()
                        field._memfile.copy('mask', group[mask_name]._memfile, 
                                            'data')
                        del field._memfile['mask']
            elif (isinstance(group.entries[key], NXentry) and 
                  not isinstance(group, NXroot)):
                  group.entries[key].nxclass = NXsubentry
            group.entries[key].update()
        else:
            raise NeXusError("Invalid key")

    def __delitem__(self, key):
        """Delete an entry in the group dictionary.
        
        Parameters
        ----------
        key : str
            Name of the NeXus field or group to be deleted.

        Notes
        -----
        If a mask is associated with a deleted field, it is also deleted.
        """
        if self.nxfilemode == 'r':
            raise NeXusError("NeXus file opened as readonly")
        if is_text(key): #i.e., deleting a NeXus object
            group = self
            if '/' in key:
                names = [name for name in key.split('/') if name]
                key = names.pop()
                for name in names:
                    if name in group:
                        group = group[name]
                    else:
                        raise NeXusError("Invalid path")
            if key not in group:
                raise NeXusError("'"+key+"' not in "+group.nxpath)
            elif group[key].is_linked():
                raise NeXusError("Cannot delete an item in a linked group")
            if group.nxfilemode == 'rw':
                with group.nxfile as f:
                    if 'mask' in group.entries[key].attrs:
                        del f[group.entries[key].mask.nxpath]
                    del f[group.entries[key].nxpath]
            if 'mask' in group.entries[key].attrs:
                del group.entries[group.entries[key].mask.nxname]
            del group.entries[key]
            group.set_changed()

    def __contains__(self, key):
        """Implements 'k in d' test using the group's entries."""
        if isinstance(self, NXroot) and key == '/':
            return True
        elif isinstance(key, NXobject):
            return id(key) in [id(x) for x in self.entries.values()]
        else:
            try:
                return isinstance(self[key], NXobject)		
            except Exception:		
                return False

    def __eq__(self, other):
        """Return True if all the group entries are the same as another."""
        if not isinstance(other, NXgroup): 
            return False
        elif id(self) == id(other):
            return True
        else:
            return self.entries == other.entries

    def __iter__(self):
        """Implement key iteration."""
        return self.entries.__iter__()

    def __len__(self):
        """Return the number of entries in the group."""
        return len(self.entries)

    def __deepcopy__(self, memo):
        """Return a deep copy of the group."""
        obj = self
        dpcpy = obj.__class__()
        dpcpy._name = self._name
        memo[id(self)] = dpcpy
        dpcpy._changed = True
        for k,v in obj.items():
            if isinstance(v, NXlink):
                v = v.nxlink
            dpcpy.entries[k] = deepcopy(v, memo)
            dpcpy.entries[k]._group = dpcpy
        for k, v in obj.attrs.items():
            dpcpy.attrs[k] = copy(v)
        if 'target' in dpcpy.attrs:
            del dpcpy.attrs['target']
        dpcpy._group = None
        return dpcpy

    def walk(self):
        """Walk through all the values in the group."""
        yield self
        for node in self.values():
            for child in node.walk():
                yield child

    def update(self):
        """Update the NXgroup, including its children, in the NeXus file."""
        if self.nxfilemode == 'rw':
            with self.nxfile as f:
                f.update(self)
        elif self.nxfilemode is None:
            for node in self.walk():
                if isinstance(node, NXfield) and node._uncopied_data:
                    node._value = node._get_uncopied_data()
        self.set_changed()

    def get(self, name, default=None):
        """Retrieve the group entry, or return default if it doesn't exist."""
        try:
            return self.entries[name]
        except KeyError:
            return default
            
    def keys(self):
        """Return the names of NeXus objects in the group."""
        return self.entries.keys()

    def iterkeys(self):
        """Return an iterator over group object names."""
        return iter(self.entries)

    def values(self):
        """Return the values of NeXus objects in the group."""
        return self.entries.values()

    def itervalues(self):
        """Return an iterator over group objects."""
        for key in self.entries:
            yield self.entries.get(key)

    def items(self):
        """Return a list of the NeXus objects as (key,value) pairs."""
        return self.entries.items()

    def iteritems(self):
        """Return an iterator over (name, object) pairs."""
        for key in self.entries:
            yield (key, self.entries.get(key))

    def has_key(self, name):
        """Return true if an object of the specified name is in the group."""
        return name in self.entries   

    def clear(self):
        raise NeXusError("This method is not implemented for NXgroups")

    def pop(self, *args, **kwargs):
        raise NeXusError("This method is not implemented for NXgroups")

    def popitem(self, *args, **kwargs):
        raise NeXusError("This method is not implemented for NXgroups")

    def fromkeys(self, *args, **kwargs):
        raise NeXusError("This method is not implemented for NXgroups")

    def setdefault(self, *args, **kwargs):
        raise NeXusError("This method is not implemented for NXgroups")

    def component(self, nxclass):
        """Return a list of entries in the group of the same class.
        
        Parameters
        ----------
        nxclass : str
            Class name
        
        Returns
        -------
        list of NXfields or NXgroups
            List of fields or groups of the same class.
        """
        return [self.entries[i] for i in sorted(self.entries, key=natural_sort)
                if self.entries[i].nxclass==nxclass]

    def move(self, item, group, name=None):
        """Move an item in the group to another group within the same tree.
        
        Parameters
        ----------
        item : NXobject or str
            Item to be moved, defined either by the item itself or by its name.
        group : NXgroup or str
            New group to contain the item.
        name : str, optional
            Name of the item in the new group. By default, the name is unchanged.
        """
        if is_text(item):
            if item in self:
                item = self[item]
            else:
                raise NeXusError("'%s' not in group" % item)
        if is_text(group):
            if group in self:
                group = self[group]
            elif group in self.nxroot:
                group = self.nxroot[group]
            else:
                raise NeXusError("'%s' not in tree" % group)
            if not isinstance(group, NXgroup):
                raise NeXusError("Destination must be a valid NeXus group")
        if item.nxroot != group.nxroot:
            raise NeXusError("The item can only be moved within the same tree")
        if name is None:
            name = item.nxname
        if name in group:
            raise NeXusError("'%s' already in the destination group")
        group[name] = item
        del self[item.nxname]

    def insert(self, value, name='unknown'):
        """Add an NeXus field or group to the current group.
        
        If it is not a valid NeXus object, the value is converted to an 
        NXfield. If the object is an internal link within an externally linked
        file, the linked object in the external file is copied.

        Parameters
        ----------
        value : NXfield or NXgroup or str or array-like
            NeXus field or group to be added.
        name : str, optional
            Name of the new entry, by default the name of the added object.
        """
        if isinstance(value, NXobject):
            if name == 'unknown': 
                name = value.nxname
            if name in self.entries:
                raise NeXusError("'%s' already exists in group" % name)
            self[name] = value
            self.update()
        else:
            if name in self.entries:
                raise NeXusError("'%s' already exists in group" % name)
            self[name] = NXfield(value=value, name=name, group=self)

    def makelink(self, target, name=None, abspath=False):
        """Create a linked NXobject within the group.

        The root of the target and the child's group must be the same.
        
        Parameters
        ----------
        target : str
            Path to the parent object.
        name : str, optional
            The name of the linked object, by default the same as the target.
        abspath : bool, optional
            True if the target is an absolute path, by default False
        """
        if isinstance(target, NXlink):
            raise NeXusError("Cannot link to an NXlink object")
        elif not isinstance(target, NXobject):
            raise NeXusError("Link target must be an NXobject")
        elif not isinstance(self.nxroot, NXroot):
            raise NeXusError(
                "The group must have a root object of class NXroot")
        elif target.is_external():
            raise NeXusError(
                "Cannot link to an object in an externally linked group")
        if name is None:
            name = target.nxname
        if name in self:
            raise NeXusError("Object with the same name already exists in '%s'" 
                             % self.nxpath)        
        if self.nxroot == target.nxroot:
            self[name] = NXlink(target=target)
        else:
            self[name] = NXlink(target=target.nxpath, file=target.nxfilename,
                                abspath=abspath)
 
    def sum(self, axis=None, averaged=False):
        """Return a sum of the signal in the group.
        
        This function should only be used on NXdata groups. The sum is over a 
        single axis or a tuple of axes using the Numpy sum method.
        
        Parameters
        ----------
        axis : int, optional
            Axis to be summed, by default all of the axes.
        averaged : bool, optional
            If True, divide the sum by the signal size, by default False.
        
        Returns
        -------
        NXdata
            Data group containin the summed values.
        
        Notes
        -----
        The result contains a copy of all the metadata contained in
        the NXdata group.
        """
        if self.nxsignal is None:
            raise NeXusError("No signal to sum")
        if not hasattr(self,"nxclass"):
            raise NeXusError("Summing not allowed for groups of unknown class")
        if axis is None:
            if averaged:
                return self.nxsignal.sum() / self.nxsignal.size
            else:
                return self.nxsignal.sum()
        else:
            if isinstance(axis, numbers.Integral):
                axis = [axis]
            axis = tuple(axis)
            signal = NXfield(self.nxsignal.sum(axis), name=self.nxsignal.nxname,
                             attrs=self.nxsignal.safe_attrs)
            axes = self.nxaxes
            averages = []
            for ax in axis:
                summedaxis = deepcopy(axes[ax])
                summedaxis.attrs["minimum"] = summedaxis.nxdata[0]
                summedaxis.attrs["maximum"] = summedaxis.nxdata[-1]
                summedaxis.attrs["summed_bins"] = summedaxis.size
                averages.append(NXfield(
                    0.5*(summedaxis.nxdata[0]+summedaxis.nxdata[-1]), 
                    name=summedaxis.nxname,attrs=summedaxis.attrs))
            axes = [axes[i] for i in range(len(axes)) if i not in axis]
            result = NXdata(signal, axes)
            summed_bins = 1
            for average in averages:
                result.insert(average)
                summed_bins *= average.attrs["summed_bins"]
            if averaged:
                result.nxsignal = result.nxsignal / summed_bins
                result.attrs["averaged_bins"] = summed_bins
            else:
                result.attrs["summed_bins"] = summed_bins
            if self.nxerrors:
                errors = np.sqrt((self.nxerrors.nxdata**2).sum(axis))
                if averaged:
                    result.nxerrors = NXfield(errors) / summed_bins
                else:
                    result.nxerrors = NXfield(errors)
            if self.nxtitle:
                result.title = self.nxtitle
            return result

    def average(self, axis=None):
        """Return the average of the signal of the group.
        
        This function should only be used on NXdata groups. The sum is over a 
        single axis or a tuple of axes using the Numpy sum method. The result 
        is then divided by the number of summed bins to produce an average.

        Parameters
        ----------
        axis : int, optional
            Axis to be averaged, by default all of the axes.
        
        Returns
        -------
        NXfield
            Averaged value.

        Notes
        -----
        The result contains a copy of all the metadata contained in
        the NXdata group.
        """
        return self.sum(axis, averaged=True)

    def moment(self, order=1, center=None):
        """Return the central moments of the one-dimensional signal.
        
        Parameters
        ----------
        order : int, optional
            Order of the calculated moment, by default 1.
        center : float, optional
            Center if defined externally for use by higher order moments,
            by default None.
        
        Returns
        -------
        NXfield
            Value of moment.
        """
        signal, axes = self.nxsignal, self.nxaxes
        if signal is None:
            raise NeXusError("No signal to calculate")
        elif len(signal.shape) > 1:
            raise NeXusError(
                "Operation only possible on one-dimensional signals")
        if not hasattr(self, "nxclass"):
            raise NeXusError(
                "Operation not allowed for groups of unknown class")
        y = signal / signal.sum()
        x = centers(axes[0], y.shape[0])
        if center:
            c = center
        else:
            c = (y * x).sum()
        if order == 1:
            return c
        else:
            return (y * (x - c)**order).sum()

    def mean(self):
        """Return the mean value of one-dimensional data.
    
        Returns
        -------
        NXfield
            The mean of the group signal.
        """
        return self.moment(1)

    def var(self):
        """Return the variance of the one-dimensional data.
        
        Returns
        -------
        NXfield
            The variance of the group signal.
        """
        return self.moment(2)

    def std(self):
        """Return the standard deviation of the one-dimensional data.
        
        Returns
        -------
        NXfield
            The standard deviation of the group signal.
        """
        return np.sqrt(self.moment(2))

    def get_default(self):
        """Return the default data group if it is defined or None.
        
        Returns
        -------
        NXdata
            Data group to be plotted.
        """
        if 'default' in self.attrs and self.attrs['default'] in self:
            default = self[self.attrs['default']]
            return default.get_default()
        else:
            return None

    def set_default(self, over=False):
        """Set the current group as the default for plotting.
        
        This function is overridden by the NXentry and NXdata classes. For all
        other groups, it raises an error.
        """
        raise NeXusError(
            "Can only set the default for NXentry and NXdata groups")

    def is_plottable(self):
        """Return True if the group contains plottable data."""
        plottable = False
        for entry in self:
            if self[entry].is_plottable():
                plottable = True
        return plottable        

    @property
    def plottable_data(self):
        """Return the first NXdata group within the group's tree."""
        return None

    def plot(self, **kwargs):
        """Plot data contained within the group.
        
        Valid keyword arguments are passed to Matplotlib.
        """
        plotdata = self.plottable_data
        if plotdata:
            plotdata.plot(**kwargs)
        else:
            raise NeXusError("There is no plottable data")

    def oplot(self, **kwargs):
        """Overplot the group signal over the current figure."""
        plotdata = self.plottable_data
        if plotdata:
            plotdata.oplot(**kwargs)
        else:
            raise NeXusError("There is no plottable data")

    def logplot(self, **kwargs):
        """Plot the group signal on a log scale."""
        plotdata = self.plottable_data
        if plotdata:
            plotdata.logplot(**kwargs)
        else:
            raise NeXusError("There is no plottable data")

    def implot(self, **kwargs):
        """Plot the group signal as an RGB(A) image."""
        plotdata = self.plottable_data
        if plotdata:
            plotdata.implot(**kwargs)
        else:
            raise NeXusError("There is no plottable data")

    def signals(self):
        """Return a dictionary of NXfield's containing signal data.

        The key is the value of the signal attribute.
        """
        signals = {}
        for obj in self.values():
            if 'signal' in obj.attrs:
                signals[obj.attrs['signal']] = obj
        return signals

    def _str_name(self, indent=0):
        return " " * indent + self.nxname + ':' + self.nxclass

    def _str_tree(self, indent=0, attrs=False, recursive=False):
        result = [self._str_name(indent=indent)]
        if self.attrs and (attrs or indent==0):
            result.append(self._str_attrs(indent=indent+2))
        entries = self.entries
        if entries:
            names = sorted(entries, key=natural_sort)
            if recursive:
                if recursive is True or recursive >= indent:
                    for k in names:
                        result.append(entries[k]._str_tree(indent=indent+2,
                                                           attrs=attrs, 
                                                           recursive=recursive))
            else:
                for k in names:
                    result.append(entries[k]._str_name(indent=indent+2))
        return "\n".join(result)

    @property
    def nxtitle(self):
        """The group title.

        If there is no title field in the group or its parent group, the 
        group's path is returned.
        """
        if 'title' in self:
            return text(self.title)
        elif self.nxgroup and 'title' in self.nxgroup:
            return text(self.nxgroup.title)
        else:
            root = self.nxroot
            if root.nxname != '' and root.nxname != 'root':
                return (root.nxname + '/' + self.nxpath.lstrip('/')).rstrip('/')
            else:
                fname = self.nxfilename
                if fname is not None:
                    return fname + ':' + self.nxpath
                else:
                    return self.nxpath

    @property
    def entries(self):
        """Dictionary of NeXus objects in the group.
        
        Returns
        -------
        dict of NXfields and/or NXgroups
            Dictionary of group objects.
        """
        return self._entries

    nxsignal = None
    nxaxes = None
    nxerrors = None


class NXlink(NXobject):
    """Parent class for NeXus linked objects.

    The link is initialized by specifying the path to the link target and,
    if the link is to an external file, the filename. When it is possible to 
    access the target, the class of the link is changed to NXlinkfield or 
    NXlinkgroup. 

    Attributes
    ----------
    nxlink : NXfield or NXgroup
        Target of link.
    """

    _class = "NXlink"

    def __init__(self, target=None, file=None, name=None, group=None, 
                 abspath=False):
        self._class = "NXlink"
        self._name = name
        self._group = group
        self._abspath = abspath
        if file is not None:
            self._filename = file
            self._mode = 'r'
        else:
            self._filename = self._mode = None
        if isinstance(target, NXobject):
            if isinstance(target, NXlink):
                raise NeXusError("Cannot link to another NXlink object")
            if name is None:
                self._name = target.nxname
            self._target = target.nxpath
            if isinstance(target, NXfield):
                self._setclass(NXlinkfield)
            elif isinstance(target, NXgroup):
                self._setclass(_getclass(target.nxclass, link=True))
        else:
            if name is None and is_text(target):
                self._name = target.rsplit('/', 1)[1]
            self._target = text(target)
            if not self._target.startswith('/'):
                self._target = '/' + self._target
        self._link = None

    def __repr__(self):
        if self._filename:
            return "NXlink(target='%s', file='%s')" % (self._target, 
                                                       self._filename)
        else:
            return "NXlink('%s')" % (self._target)

    def __getattr__(self, name):
        """Return the requested attribute from the target object.

        The value of the corresponding target attribute is returned, reading
        from the external file if necessary. 
        """
        try:
            return getattr(self.nxlink, name)
        except Exception as error:
            raise NeXusError("Cannot resolve the link to '%s'" % self._target)

    def __setattr__(self, name, value):
        """Set an attribute of the link target.
        
        This is not allowed when the target is in an external file. 

        Parameters
        ----------
        name : str
            Name of the attribute
        value : NXfield or NXgroup or NXattr or str or array-like
            Value to be assigned to the attribute. 
        """
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        elif self.is_external():
            raise NeXusError("Cannot modify an external link")
        else:
            try:
                self.nxlink.setattr(name, value)
            except Exception as error:
                raise NeXusError("Unable to modify link target")

    def __setitem__(self, idx, value):
        """Assign values to a slice of the target NXfield.
        
        Parameters
        ----------
        idx : slice
            Slice to be modified.
        value
            Value to be added. The value must be compatible with the NXfield
            dtype and it must be possible to broadcast it to the shape of the 
            specified slice.
        """
        if self.is_external():
            raise NeXusError("Cannot modify an externally linked file")
        else:
            self.nxlink.__setitem__(idx, value)

    def __deepcopy__(self, memo={}):
        """Return a deep copy of the link containing the target information."""
        obj = self
        dpcpy = obj.__class__()
        memo[id(self)] = dpcpy
        dpcpy._name = copy(self.nxname)
        dpcpy._target = copy(obj._target)
        if obj._filename:
            dpcpy._filename = copy(obj.nxfilename)
        else:
            dpcpy._filename = None
        dpcpy._abspath = copy(obj._abspath)
        dpcpy._link = None
        dpcpy._group = None
        return dpcpy

    def _str_name(self, indent=0):
        if self._filename:
            return (" " * indent + self.nxname + ' -> ' + text(self._filename) +
                    "['" + text(self._target) + "']")
        else:
            return " " * indent + self.nxname + ' -> ' + text(self._target)

    def _str_tree(self, indent=0, attrs=False, recursive=False):
        return self._str_name(indent=indent)

    def update(self):
        """Update the NeXus file if necessary."""
        root = self.nxroot
        filename, mode = root.nxfilename, root.nxfilemode
        if (filename is not None and os.path.exists(filename) and mode == 'rw'):
            with root.nxfile as f:
                f.update(self)
        self.set_changed()

    @property
    def nxlink(self):
        """Target of link.
        
        If called for the first time, this attempts to initialize the link 
        class (NXlinkfield or NXlinkgroup) and attributes if the target
        is accessible.
        """
        self.initialize_link()
        if self._link is None:
            if self.is_external():
                self._link = self.external_link
            else:
                self._link = self.internal_link
        return self._link

    def initialize_link(self):
        """Resolve the link class and read in key attributes.
        
        Returns
        -------
        NXfield or NXgroup
            Target of link.
        """
        if self.nxclass == 'NXlink':
            if self.is_external():
                if os.path.exists(self.nxfilename):
                    with self.nxfile as f:
                        item = f.readpath(self.nxfilepath)
                else:
                    return
            elif self._target in self.nxroot:
                item = self.nxroot[self._target]
            else:
                return
            if isinstance(item, NXfield):
                self._setclass(NXlinkfield)
            elif isinstance(item, NXgroup):
                self._setclass(_getclass(item.nxclass, link=True))
            else:
                return

    @property
    def internal_link(self):
        return self.nxroot[self._target]

    @property
    def external_link(self):
        try:
            with self.nxfile as f:
                item = f.readpath(self.nxfilepath)
            return item
        except Exception as error:
            raise NeXusError("Cannot read the external link to '%s'" 
                             % self._filename)

    @property
    def attrs(self):
        try:
            return self.nxlink.attrs
        except NeXusError:
            return AttrDict()

    @property
    def nxfilemode(self):
        """Read/write mode of the NeXus file if saved to a file.

        Notes
        -----
        External links are always read-only.
        """
        try:
            if self.is_external():
                return 'r'
            else:
                return self.nxlink.nxfilemode
        except Exception:
            return 'r'

    @property
    def abspath(self):
        """True if the filename is to be stored as an absolute path."""
        return self._abspath


class NXlinkfield(NXlink, NXfield):
    """Class for NeXus linked fields."""

    def __init__(self, target=None, file=None, name=None, abspath=False, 
                 **kwargs):
        NXlink.__init__(self, target=target, file=file, name=name, 
                        abspath=abspath)
        self._class = "NXfield"


class NXlinkgroup(NXlink, NXgroup):
    """Class for NeXus linked groups."""

    def __init__(self, target=None, file=None, name=None, abspath=False, 
                 **kwargs):
        NXlink.__init__(self, target=target, file=file, name=name, 
                        abspath=abspath)
        if 'nxclass' in kwargs:
            self._setclass(_getclass(kwargs['nxclass'], link=True))
        else:
            self._class = 'NXlink'
        self._entries = {}

    def __getattr__(self, name):
        """Return attribute looking in the group entries and attributes.

        If the attribute is the name of a defined NeXus class, a list of group
        entries of that class are returned.
        """
        return NXgroup(self).__getattr__(name)

    def _str_name(self, indent=0):
        if self._filename:
            return (" " * indent + self.nxname + ':' + self.nxclass + 
                    ' -> ' + text(self._filename) + 
                    "['" + text(self._target) + "']")
        else:
            return (" " * indent + self.nxname + ':' + self.nxclass + 
                    ' -> ' + text(self._target))

    def _str_tree(self, indent=0, attrs=False, recursive=False):
        try:
            return NXgroup._str_tree(self, indent=indent, attrs=attrs, 
                                     recursive=recursive)
        except Exception:
            return NXlink(self)._str_tree(self, indent=indent)

    @property
    def entries(self):
        """Dictionary of NeXus objects in the linked group.
        
        Returns
        -------
        dict of NXfields and/or NXgroups
            Dictionary of group objects.
        """
        _linked_entries = self.nxlink.entries
        _entries = {}
        if self.is_external():
            for entry in _linked_entries:
                _entries[entry] = _linked_entries[entry]
                _entries[entry]._group = self
        else:            
            for entry in _linked_entries:
                _entries[entry] = deepcopy(_linked_entries[entry])
                _entries[entry]._group = self
        return _entries


class NXroot(NXgroup):
    """NXroot group, a subclass of the `NXgroup` class.

    This group has additional methods to lock or unlock the tree.
    """

    def __init__(self, *args, **kwargs):
        self._class = "NXroot"
        self._backup = None
        self._mtime = None
        self._file_modified = False
        NXgroup.__init__(self, *args, **kwargs)

    def reload(self):
        """Reload the NeXus file from disk."""
        if self.nxfilemode:
            with self.nxfile as f:
                f.reload()
            self.set_changed()
        else:
            raise NeXusError("'%s' has no associated file to reload" 
                              % self.nxname)

    def is_modified(self):
        """True if the NeXus file has been modified by an external process."""
        try:
            _mtime = self.nxfile.mtime
            if self._mtime and _mtime > self._mtime:
                self._file_modified = True
                return True
            else:
                self._file_modified = False
                return False
        except (AttributeError, TypeError, FileNotFoundError):
            self._file_modified = False
            return False

    def lock(self):
        """Make the tree readonly."""
        if self._filename:
            if self.file_exists():
                self._mode = self._file.mode = 'r'
                self.set_changed()
            else:
                raise NeXusError("'%s' does not exist"
                                 % os.path.abspath(self.nxfilename))

    def unlock(self):
        """Make the tree modifiable."""
        if self._filename:
            if self.file_exists():
                if self.is_modified():
                    raise NeXusError("File modified. Reload before unlocking")
                self._mode = self._file.mode = 'rw'
            else:
                self._mode = None
                self._file = None
                raise NeXusError("'%s' does not exist"
                                 % os.path.abspath(self.nxfilename))
            self.set_changed()

    def backup(self, filename=None, dir=None):
        """Backup the NeXus file.
        
        Parameters
        ----------
        filename : str, optional
            Name of file to contain the backup. If not specified, the backup is 
            saved with a randomized name.
        dir : str, optional
            Directory to contain the backup, by default the current directory.
        """ 
        if self.nxfilemode is None:
            raise NeXusError("Only data saved to a NeXus file can be backed up")
        if filename is None:
            if dir is None:
                dir = os.getcwd()
            import tempfile
            prefix, suffix = os.path.splitext(os.path.basename(self.nxfilename))
            prefix = prefix + '_backup_'
            backup = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=dir)[1]
        else:
            if dir is not None:
                filename = os.path.join(dir, filename)
            if os.path.exists(filename):
                raise NeXusError("'%s' already exists" 
                                 % os.path.abspath(filename))
            else:
                backup = os.path.abspath(filename)
        import shutil
        shutil.copy2(self.nxfilename, backup)
        self._backup = backup

    def restore(self, filename=None, overwrite=False):
        """Restore a backup.
        
        Parameters
        ----------
        filename : str, optional
            Name of file to restore the backup to. If no file name is given, 
            the backup replaces the current NeXus file, provided 'overwrite' 
            has been set to True.
        overwrite : bool, optional
            True if the file is to be overwritten, by default False
        """
        if self._backup is None:
            raise NeXusError("No backup exists")
        if filename is None:
            filename = self.nxfilename
        if os.path.exists(filename) and not overwrite:
            raise NeXusError("To overwrite '%s', set 'overwite' to True"
                             % os.path.abspath(filename))
        import shutil
        shutil.copy2(self._backup, filename)
        self.nxfile = filename

    def close(self):
        """Close the underlying HDF5 file."""
        if self.nxfile:
            self.nxfile.close()

    def set_default(self, over=False):
        """Override function to set default for plotting.
        
        Parameters
        ==========
        over : bool
            True if previous default should be overwritten
        """
        pass

    @property
    def plottable_data(self):
        """The default data group to be plotted in this tree.
        
        This will return the default group if the `default` attribute has been
        set. Otherwise, the first NXdata, NXmonitor, or NXlog group will be 
        returned.
        
        Returns
        -------
        NXdata
            Data group to be plotted.
        """
        default = self.get_default()
        if default is not None:
            return default
        elif self.NXdata:
            return self.NXdata[0]
        elif self.NXmonitor:
            return self.NXmonitor[0]
        elif self.NXlog:
            return self.NXlog[0]
        elif self.NXentry:
            for entry in self.NXentry:
                data = entry.plottable_data
                if data is not None:
                    return data
        return None

    @property
    def nxfile(self):
        """NXFile storing the NeXus data."""
        if self._file:
            return self._file
        elif self._filename:
            self._file = NXFile(self._filename, self._mode)
            return self._file
        else:
            return None

    @nxfile.setter
    def nxfile(self, filename):
        if os.path.exists(filename):
            self._filename = os.path.abspath(filename)
            with NXFile(self._filename, 'r') as f:
                root = f.readfile()
            self._entries = root._entries
            for entry in self._entries:
                self._entries[entry]._group = self
            self._attrs._setattrs(root.attrs)
            self._file = NXFile(self._filename, self._mode)
            self.set_changed()
        else:
            raise NeXusError("'%s' does not exist" % os.path.abspath(filename))

    @property
    def nxbackup(self):
        """Path to the backup file if it exists."""
        return self._backup

    @property
    def mtime(self):
        """Modification time of the last change to root group."""
        return self._mtime


class NXentry(NXgroup):
    """NXentry group, a subclass of the NXgroup class."""

    def __init__(self, *args, **kwargs):
        self._class = "NXentry"
        NXgroup.__init__(self, *args, **kwargs)

    def __add__(self, other):
        """Add two NXentry groups.
        
        All NXdata groups are added together. All other entries are copied from
        the current NXentry.
        
        Parameters
        ----------
        other : NXentry
            Entry to be added.
        
        Returns
        -------
        NXentry
            Group after addition.
        """
        result = NXentry(attrs=self.attrs)
        try:
            names = [name for name in self if 
                     (isinstance(self[name], NXdata) or
                      isinstance(self[name], NXmonitor))]
            for name in names:
                if isinstance(other[name], NXdata):
                    result[name] = self[name] + other[name]
                else:
                    raise KeyError
            for name in [name for name in self if name not in names]:
                result[name] = self[name]
            return result
        except KeyError:
            raise NeXusError("Inconsistency between two NXentry groups")

    def __sub__(self, other):
        """Subtract another NXentry group from the current NXentry.
        
        All NXdata groups are subtracted. All other entries are copied from
        the current NXentry.
                
        Parameters
        ----------
        other : NXentry
            Entry to be subtracted.
        
        Returns
        -------
        NXentry
            Group after subtraction.
        """
        result = NXentry(attrs=self.attrs)
        try:
            names = [name for name in self if isinstance(self[name], NXdata)]
            for name in names:
                if isinstance(other[name], NXdata):
                    result[name] = self[name] - other[name]
                else:
                    raise KeyError
            for name in [name for name in self 
                         if not isinstance(self[name], NXdata)]:
                result[name] = self[name]
            return result
        except KeyError:
            raise NeXusError("Inconsistency between two NXentry groups")

    def set_default(self, over=False):
        """Set group as the default for plotting.
        
        This will set defaults for parents of the parent group unless they have
        been set previously.
        
        Parameters
        ==========
        over : bool
            True if previous default should be overwritten
        """
        group = self.nxgroup
        if group is None:
            raise NeXusError(
                "The default cannot be defined without a parent group")
        elif isinstance(group, NXentry) or isinstance(group, NXroot):
            group.attrs['default'] = self.nxname
            parent_group = group.nxgroup
            if parent_group:
                if over or parent_group.get_default() is None:
                    group.set_default(over=over)
        else:
            raise NeXusError(
                "The default can only be defined in a NXentry or NXroot group")

    @property
    def plottable_data(self):
        """The default data group to be plotted in this entry.
        
        This will return the default group if the `default` attribute has been
        set. Otherwise, the first NXdata, NXmonitor, or NXlog group will be 
        returned.
        """
        default = self.get_default()
        if default is not None:
            return default
        elif self.NXdata:
            return self.NXdata[0]
        elif self.NXmonitor:
            return self.NXmonitor[0]
        elif self.NXlog:
            return self.NXlog[0]
        else:
            return None


class NXsubentry(NXentry):
    """NXsubentry group, a subclass of the NXsubentry class."""

    def __init__(self, *args, **kwargs):
        self._class = "NXsubentry"
        NXgroup.__init__(self, *args, **kwargs)


class NXdata(NXgroup):
    """NXdata group, a subclass of the NXgroup class.

    The constructor assumes that the first argument contains the signal and
    the second contains either the axis, for one-dimensional data, or a list
    of axes, for multidimensional data. These arguments can either be NXfield
    objects or Numpy arrays, which are converted to NXfield objects with default
    names. Alternatively, the signal and axes NXfields can be defined using the
    'nxsignal' and 'nxaxes' properties. See the examples below.
    
    Various arithmetic operations (addition, subtraction, multiplication,
    and division) have been defined for combining NXdata groups with other
    NXdata groups, Numpy arrays, or constants, raising a NeXusError if the
    shapes don't match. Data errors are propagated in quadrature if
    they are defined, i.e., if the 'nexerrors' attribute is not None,

    Parameters
    ----------
    signal : NXfield
        Field defining the data to be plotted.
    axes : tuple of NXfields
        Tuple of one-dimensional fields defining the plot axes in the order of 
        the corresponding signal dimensions.
    errors : NXfield, optional
        Field containing the standard deviations of the signal values.

    Attributes
    ----------
    nxsignal : NXfield
        The NXfield containing the data to be plotted.
    nxaxes : tuple of NXfields
        A tuple of NXfields containing the plot axes
    nxerrors : NXfield
        The NXfield containing the standard deviations of the signal values.

    Examples
    --------
    There are three methods of creating valid NXdata groups with the
    signal and axes NXfields defined according to the NeXus standard.
    
    1) Create the NXdata group with Numpy arrays that will be assigned
       default names.
       
       >>> x = np.linspace(0, 2*np.pi, 101)
       >>> line = NXdata(sin(x), x)
       data:NXdata
         signal = float64(101)
           @axes = x
           @signal = 1
         axis1 = float64(101)
      
    2) Create the NXdata group with NXfields that have their internal
       names already assigned.

       >>> x = NXfield(linspace(0,2*pi,101), name='x')
       >>> y = NXfield(linspace(0,2*pi,101), name='y')    
       >>> X, Y = np.meshgrid(x, y)
       >>> z = NXfield(sin(X) * sin(Y), name='z')
       >>> entry = NXentry()
       >>> entry.grid = NXdata(z, (x, y))
       >>> grid.tree()
       entry:NXentry
         grid:NXdata
           x = float64(101)
           y = float64(101)
           z = float64(101x101)
             @axes = x:y
             @signal = 1

    3) Create the NXdata group with keyword arguments defining the names 
       and set the signal and axes using the nxsignal and nxaxes properties.

       >>> x = linspace(0,2*pi,101)
       >>> y = linspace(0,2*pi,101)  
       >>> X, Y = np.meshgrid(x, y)
       >>> z = sin(X) * sin(Y)
       >>> entry = NXentry()
       >>> entry.grid = NXdata(z=sin(X)*sin(Y), x=x, y=y)
       >>> entry.grid.nxsignal = entry.grid.z
       >>> entry.grid.nxaxes = [entry.grid.x,entry.grid.y]
       >>> grid.tree()
       entry:NXentry
         grid:NXdata
           x = float64(101)
           y = float64(101)
           z = float64(101x101)
             @axes = x:y
             @signal = 1
    """

    def __init__(self, signal=None, axes=None, errors=None, *args, **kwargs):
        self._class = 'NXdata'
        NXgroup.__init__(self, *args, **kwargs)
        attrs = {}
        if axes is not None:
            if not is_iterable(axes):
                axes = [axes]
            axis_names = {}
            i = 0
            for axis in axes:
                i += 1
                if isinstance(axis, NXfield) or isinstance(axis, NXlink):
                    if axis.nxname == 'unknown' or axis.nxname in self: 
                        axis_name = 'axis%s' % i
                    else:
                        axis_name = axis.nxname
                else:
                    axis_name = 'axis%s' % i
                self[axis_name] = axis
                axis_names[i] = axis_name
            attrs['axes'] = list(axis_names.values())
        if signal is not None:
            if isinstance(signal, NXfield) or isinstance(signal, NXlink):
                if signal.nxname == 'unknown' or signal.nxname in self:
                    signal_name = 'signal'
                else:
                    signal_name = signal.nxname
            else:
                signal_name = 'signal'
            self[signal_name] = signal
            attrs['signal'] = signal_name
            if errors is not None:
                if isinstance(errors, NXfield) or isinstance(errors, NXlink):
                    if errors.nxname == 'unknown' or errors.nxname in self:
                        errors_name = signal_name+'_errors'
                    else:
                        errors_name = errors.nxname
                else:
                    errors_name = signal_name+'_errors'
                self[errors_name] = errors
                self[signal_name].attrs['uncertainties'] = errors_name
        self.attrs._setattrs(attrs)

    def __setattr__(self, name, value):
        """Set a group attribute.
        
        This sets attributes the same way as the `NXgroup` class, unless the
        name is "mask", which is set by its property setter. 
        
        Parameters
        ----------
        name : str
            Name of the attribute.
        value : NXfield or NXgroup or NXattr or str or array-like
            Value of the attribute.
        """
        if name == 'mask':
            object.__setattr__(self, name, value)
        else:
            super(NXdata, self).__setattr__(name, value)

    def __getitem__(self, key):
        """Return an entry in the group or a NXdata group containing a slice.
        
        Parameters
        ----------
        key : str or slice
            If 'key' is a string, the entry of the same name is returned. If
            'key' is a slice, a NXdata group containing requested slab is
            returned. 
        
        Returns
        -------
        NXfield or NXgroup or NXdata
            Nexus entry in the group or a group containing sliced data.

        Notes
        -----
        In most cases, the slice values are applied to the NXfield array
        and returned within a new NXfield with the same metadata. However,
        if any of the index start or stop values are real, the NXfield is 
        returned with values between the limits set by the corresponding axes.
        """
        if is_text(key): #i.e., requesting a dictionary value
            return NXgroup.__getitem__(self, key)
        elif self.nxsignal is not None:
            idx, axes = self.slab(key)
            removed_axes = []
            for axis in axes:
                if axis.shape == () or axis.shape == (0,) or axis.shape == (1,):
                    removed_axes.append(axis)
            axes = [ax for ax in axes if ax not in [rax for rax in removed_axes 
                                                    if rax is ax]]            
            signal = self.nxsignal[idx]
            if self.nxerrors: 
                errors = self.nxerrors[idx]
            else:
                errors = None
            if 'axes' in signal.attrs:
                del signal.attrs['axes']
            result = NXdata(signal, axes, errors, *removed_axes)
            if errors is not None:
                result.nxerrors = errors
            if self.nxsignal.mask is not None:
                if isinstance(self.nxsignal.mask, NXfield):
                    result[self.nxsignal.mask.nxname] = signal.mask 
            if self.nxtitle:
                result.title = self.nxtitle
            return result
        else:
            raise NeXusError("No signal specified")

    def __setitem__(self, idx, value):
        """Set the values of a slab defined by a slice
        
        Parameters
        ----------
        idx : slice
            Index of values to be assigned the value.
        value : array-like
            The values to be assigned. Their shape should match the index or 
            be compatible with the usual Numpy broadcasting rules.

        Notes
        -----
        In most cases, the slice values define the indices of the signal slab.
        However, if the index start or stop values of any dimension are real, 
        that dimension's slice is determined from the indices of the 
        corresponding axis with the requested values.
        """
        if is_text(idx):
            NXgroup.__setitem__(self, idx, value)
        elif self.nxsignal is not None:
            if isinstance(idx, numbers.Integral) or isinstance(idx, slice):
                axis = self.nxaxes[0]
                if self.nxsignal.shape[0] == axis.shape[0]:
                    axis = axis.boundaries()
                idx = convert_index(idx, axis)
                self.nxsignal[idx] = value
            else:
                slices = []
                axes = self.nxaxes
                for i,ind in enumerate(idx):
                    if self.nxsignal.shape[i] == axes[i].shape[0]:
                        axis = axes[i].boundaries()
                    else:
                        axis = axes[i]
                    ind = convert_index(ind, axis)
                    if isinstance(ind, slice) and ind.stop is not None:
                        ind = slice(ind.start, ind.stop-1, ind.step)
                    slices.append(ind)
                self.nxsignal[tuple(slices)] = value
        else:
            raise NeXusError("Invalid index")

    def __delitem__(self, key):
        """Delete an entry in the current group.
        
        If the entry is a signal, the 'signal' attribute is also deleted. If 
        the entry is an axis, its entry in the 'axes' attribute array is 
        replaced by '.', designating an undefined axis.
        
        Parameters
        ----------
        key : str
            Name of the group entry to be deleted.
        """
        super(NXdata, self).__delitem__(key)
        if 'signal' in self.attrs and self.attrs['signal'] == key:
            del self.attrs['signal']
        elif 'axes' in self.attrs:
            self.attrs['axes'] = [ax if ax != key else '.'
                                  for ax in _readaxes(self.attrs['axes'])]

    def __add__(self, other):
        """Add the current data group to another NXdata group or an array.

        The result contains a copy of all the metadata contained in
        the first NXdata group. The module checks that the dimensions are
        compatible, but does not check that the NXfield names or values are
        identical. This is so that spelling variations or rounding errors
        do not make the operation fail. However, it is up to the user to
        ensure that the results make sense.

        Parameters
        ----------
        other : NXdata or array-like
            NXdata group to be added to the current group or values to be 
            added to the signal.
        
        Returns
        -------
        NXdata
            NXdata group with the summed data.
        """
        result = deepcopy(self)
        if isinstance(other, NXdata):
            if self.nxsignal and self.nxsignal.shape == other.nxsignal.shape:
                result[self.nxsignal.nxname] = self.nxsignal + other.nxsignal
                if self.nxerrors:
                    if other.nxerrors:
                        result.nxerrors = np.sqrt(self.nxerrors**2 + 
                                                  other.nxerrors**2)
                    else:
                        result.nxerrors = self.nxerrors
                return result
        elif isinstance(other, NXgroup):
            raise NeXusError("Cannot add two arbitrary groups")
        else:
            result[self.nxsignal.nxname] = self.nxsignal + other
            return result

    def __sub__(self, other):
        """Subtract another NXdata group or array values from the current group.
        
        The result contains a copy of all the metadata contained in
        the first NXdata group. The module checks that the dimensions are
        compatible, but does not check that the NXfield names or values are
        identical. This is so that spelling variations or rounding errors
        do not make the operation fail. However, it is up to the user to
        ensure that the results make sense.

        Parameters
        ----------
        other : NXdata or array-like
            Values to be subtracted from the current group.
        
        Returns
        -------
        NXdata
            NXdata group containing the subtracted data.
        """
        result = deepcopy(self)
        if isinstance(other, NXdata):
            if self.nxsignal and self.nxsignal.shape == other.nxsignal.shape:
                result[self.nxsignal.nxname] = self.nxsignal - other.nxsignal
                if self.nxerrors:
                    if other.nxerrors:
                        result.nxerrors = np.sqrt(self.nxerrors**2 + 
                                                  other.nxerrors**2)
                    else:
                        result.nxerrors = self.nxerrors
                return result
        elif isinstance(other, NXgroup):
            raise NeXusError("Cannot subtract two arbitrary groups")
        else:
            result[self.nxsignal.nxname] = self.nxsignal - other
            return result

    def __mul__(self, other):
        """Multiply the current group by another NXdata group or an array.
        
        The result contains a copy of all the metadata contained in
        the first NXdata group. The module checks that the dimensions are
        compatible, but does not check that the NXfield names or values are
        identical. This is so that spelling variations or rounding errors
        do not make the operation fail. However, it is up to the user to
        ensure that the results make sense.

        Parameters
        ----------
        other : NXdata or array-like
            Other values to multiply the data by.
        
        Returns
        -------
        NXdata
            NXdata group with the multiplied data.
        """
        result = deepcopy(self)
        if isinstance(other, NXdata):
            # error here signal not defined in this scope
            #if self.nxsignal and signal.shape == other.nxsignal.shape:
            if self.nxsignal and self.nxsignal.shape == other.nxsignal.shape:
                result[self.nxsignal.nxname] = self.nxsignal * other.nxsignal
                if self.nxerrors:
                    if other.nxerrors:
                        result.nxerrors = np.sqrt(
                                          (self.nxerrors * other.nxsignal)**2 +
                                          (other.nxerrors * self.nxsignal)**2)
                    else:
                        result.nxerrors = self.nxerrors
                return result
        elif isinstance(other, NXgroup):
            raise NeXusError("Cannot multiply two arbitrary groups")
        else:
            result[self.nxsignal.nxname] = self.nxsignal * other
            if self.nxerrors:
                result.nxerrors = self.nxerrors * other
            return result

    def __rmul__(self, other):
        """Multiply the current group by another NXdata group or an array.
        
        This variant makes __mul__ commutative.

        Parameters
        ----------
        other : NXdata or array-like
            Other values to multiply the data by.
        
        Returns
        -------
        NXdata
            NXdata group with the multiplied data.
        """
        return self.__mul__(other)

    def __truediv__(self, other):
        """Divide the current group by another NXdata group or an array.
        
        The result contains a copy of all the metadata contained in
        the first NXdata group. The module checks that the dimensions are
        compatible, but does not check that the NXfield names or values are
        identical. This is so that spelling variations or rounding errors
        do not make the operation fail. However, it is up to the user to
        ensure that the results make sense.

        Parameters
        ----------
        other : NXdata or array-like
            Other values to divide the data by.
        
        Returns
        -------
        NXdata
            NXdata group with the multiplied data.
        """
        result = deepcopy(self)
        if isinstance(other, NXdata):
            if self.nxsignal and self.nxsignal.shape == other.nxsignal.shape:
                result[self.nxsignal.nxname] = self.nxsignal / other.nxsignal
                if self.nxerrors:
                    if other.nxerrors:
                        result.nxerrors = (np.sqrt(self.nxerrors**2 +
                            (result[self.nxsignal.nxname] * other.nxerrors)**2)
                                         / other.nxsignal)
                    else:
                        result.nxerrors = self.nxerrors
                return result
        elif isinstance(other, NXgroup):
            raise NeXusError("Cannot divide two arbitrary groups")
        else:
            result[self.nxsignal.nxname] = self.nxsignal / other
            if self.nxerrors: 
                result.nxerrors = self.nxerrors / other
            return result

    __div__ = __truediv__

    def prepare_smoothing(self):
        """Create a smooth interpolation function for one-dimensional data."""
        if self.nxsignal.ndim > 1:
            raise NeXusError("Can only smooth 1D data")
        from scipy.interpolate import interp1d
        signal, axes = self.nxsignal, self.nxaxes
        x, y = centers(axes[0], signal.shape[0]), signal
        self._smoothing = interp1d(x, y, kind='cubic')

    def smooth(self, n=1000, xmin=None, xmax=None):
        """Return a NXdata group containing smooth interpolations of 1D data.
        
        Parameters
        ----------
        n : int, optional
            Number of x-values in interpolation, by default 1000
        xmin : float, optional
            Minimum x-value, by default None
        xmax : float, optional
            Maximum x-value, by default None

        Returns
        -------
        NXdata
            NeXus group containing the interpolated data
        """
        if self._smoothing is None:
            self.prepare_smoothing()
        signal, axis = self.nxsignal, self.nxaxes[0]
        x = centers(axis, signal.shape[0])
        if xmin is None:
            xmin = x.min()
        else:
            xmin = max(xmin, x.min())
        if xmax is None:
            xmax = x.max()
        else:
            xmax = min(xmax, x.max())
        xs = NXfield(np.linspace(xmin, xmax, n), name=axis.nxname)
        ys = NXfield(self._smoothing(xs), name=signal.nxname)
        return NXdata(ys, xs)      

    def project(self, axes, limits=None, summed=True):
        """Return a projection of the data with specified axes and limits.
        
        This function is used to create two-dimensional projections of two- or
        higher-dimensional data. The axes can be in any order. The limits are
        defined for all the dimensions. They either define the axis limits in
        the two-dimensional projection or the range over which the data are 
        summed or averaged for additional dimensions.

        Parameters
        ----------
        axes : tuple of ints
            Axes to be used in the two-dimensional projection.
        limits : tuple
            A tuple of minimum and maximum values for each dimension. By
            default, all values are set to None. For signals of greater than 
            two dimensions, this sums all the data in the orthogonal dimensions.
        summed : bool, optional
            True if the data is summed over the limits, False if the data is 
            averaged, by default True. 
        
        Returns
        -------
        NXdata
            NXdata group containing the projection.

        Notes
        -----
        Using the default `limits=None` should be used with caution, since it
        requires reading the entire data set into memory.
        """
        signal_rank = self.ndim
        if not is_iterable(axes):
            axes = [axes]
        if limits is None:
            limits = [(None, None)] * signal_rank
        elif len(limits) < signal_rank:
            raise NeXusError("Too few limits specified")
        elif len(axes) > 2:
            raise NeXusError(
                "Projections to more than two dimensions not supported")
        projection_axes =  sorted([x for x in range(len(limits)) 
                                   if x not in axes], reverse=True)
        idx, _ = self.slab([slice(_min, _max) for _min, _max in limits])
        result = self[idx]
        idx, slab_axes = list(idx), list(projection_axes)
        for slab_axis in slab_axes:
            if isinstance(idx[slab_axis], numbers.Integral):
                idx.pop(slab_axis)
                projection_axes.pop(projection_axes.index(slab_axis))
                for i in range(len(projection_axes)):
                    if projection_axes[i] > slab_axis:
                        projection_axes[i] -= 1
        if projection_axes:
            if summed:
                result = result.sum(projection_axes)
            else:
                result = result.average(projection_axes)
        if len(axes) > 1 and axes[0] > axes[1]:
            signal, errors = result.nxsignal, result.nxerrors
            result[signal.nxname].replace(signal.transpose())
            result.nxsignal = result[signal.nxname]
            if errors:
                result[errors.nxname].replace(errors.transpose())
                result.nxerrors = result[errors.nxname]
            result.nxaxes = result.nxaxes[::-1]            
        return result        

    def slab(self, idx):
        """Return a tuple containing the signal slice and sliced axes.
        
        Real values in the slice objects are converted to array indices 
        given by the axis values of the corresponding dimension.
        
        Parameters
        ----------
        idx : slice
            Indices of the slab.
        
        Returns
        -------
        tuple
            Tuple containing the signal slice and a list of sliced axes.
        """
        if (isinstance(idx, numbers.Real) or isinstance(idx, numbers.Integral)
                or isinstance(idx, slice)):
            idx = [idx]
        signal = self.nxsignal
        axes = self.nxaxes
        slices = []
        for i,ind in enumerate(idx):
            if is_real_slice(ind):
                if signal.shape[i] == axes[i].shape[0]:
                    axis = axes[i].boundaries()
                else:
                    axis = axes[i]
                ind = convert_index(ind, axis)
                if signal.shape[i] < axes[i].shape[0]:
                    axes[i] = axes[i][ind]
                    if isinstance(ind, slice) and ind.stop is not None:
                        ind = slice(ind.start, ind.stop-1, ind.step)
                elif (signal.shape[i] == axes[i].shape[0]):
                    if isinstance(ind, slice) and ind.stop is not None:
                        ind = slice(ind.start, ind.stop-1, ind.step)
                    axes[i] = axes[i][ind]
                slices.append(ind)
            else:
                ind = convert_index(ind, axes[i])
                slices.append(ind)
                if (isinstance(ind, slice) and ind.stop is not None
                    and signal.shape[i] < axes[i].shape[0]):
                    ind = slice(ind.start, ind.stop+1, ind.step)
                axes[i] = axes[i][ind]
        return tuple(slices), axes

    def get_default(self):
        """Return this NXdata group as the default for plotting."""
        return self

    def set_default(self, over=False):
        """Set group as the default for plotting.
        
        Parameters
        ==========
        over : bool
            True if previous default should be overwritten
        """
        group = self.nxgroup
        if group is None:
            raise NeXusError(
                "The default cannot be defined without a parent group")
        elif isinstance(group, NXentry) or isinstance(group, NXroot):
            group.attrs['default'] = self.nxname
            parent_group = group.nxgroup
            if parent_group:
                if over or parent_group.get_default() is None:
                    group.set_default(over=over)
        else:
            raise NeXusError(
                "The default can only be defined in a NXentry or NXroot group")

    @property
    def plottable_data(self):
        """True if the NXdata group is plottable."""
        if self.nxsignal is not None:
            return self
        else:
            return None

    @property
    def plot_shape(self):
        """Shape of plottable data.
        
        Size-one axes are removed from the shape.
        """
        if self.nxsignal is not None:
            return self.nxsignal.plot_shape
        else:
            return None

    @property
    def plot_rank(self):
        """Rank of the plottable data.
        
        Size-one axes are removed from the rank.
        """
        if self.nxsignal is not None:
            return self.nxsignal.plot_rank
        else:
            return None

    @property
    def plot_axes(self):
        """Plottable axes.
        
        Size-one axes are removed.
        """
        signal = self.nxsignal
        if signal is not None:
            if len(signal.shape) > len(signal.plot_shape):
                axes = self.nxaxes
                newaxes = []
                for i in range(signal.ndim):
                    if signal.shape[i] > 1: 
                        newaxes.append(axes[i])
                return newaxes
            else:
                return self.nxaxes
        else:
            return None

    def is_image(self):
        """True if the data are compatible with an RGB(A) image."""
        signal = self.nxsignal
        if signal is not None:
            return signal.is_image()
        else:
            return False

    def plot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
             vmin=None, vmax=None, **kwargs):
        """Plot the NXdata group.
        
        The format argument is used to set the color and type of the
        markers or lines for one-dimensional plots, using the standard 
        Matplotlib syntax. The default is set to blue circles. All 
        keyword arguments accepted by matplotlib.pyplot.plot can be
        used to customize the plot.
        
        Parameters
        ----------
        fmt : str, optional
            Matplotlib format string, by default ''
        xmin : float, optional
            Minimum x-value in plot, by default None
        xmax : float, optional
            Maximum x-value in plot, by default None
        ymin : float, optional
            Minimum y-value in plot, by default None
        ymax : float, optional
            Maximum y-value in plot, by default None
        vmin : float, optional
            Minimum signal value for 2D plots, by default None
        vmax : float, optional
            Maximum signal value for 2D plots, by default None

        Notes
        -----
        In addition to the Matplotlib keyword arguments, the following
        are defined ::
        
            log = True     - plot the intensity on a log scale
            logy = True    - plot the y-axis on a log scale
            logx = True    - plot the x-axis on a log scale
            over = True    - plot on the current figure
            image = True   - plot as an RGB(A) image
        """
        signal = self.nxsignal
        if signal is None:
            raise NeXusError("No plotting signal defined")
        elif not signal.exists():
            raise NeXusError("Data for '%s' does not exist" % signal.nxpath)
        elif not signal.is_plottable():
            raise NeXusError("'%s' is not plottable" % signal.nxpath)
        else:
            axes = self.plot_axes
            if axes is not None and not self.nxsignal.valid_axes(axes):
                raise NeXusError("Defined axes not compatible with the signal")

        # Plot with the available plotter
        try:
            from __main__ import plotview
            if plotview is None:
                raise ImportError
        except ImportError:
            from .plot import plotview
            
        plotview.plot(self, fmt, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, 
                      vmin=vmin, vmax=vmax, **kwargs)
    
    def oplot(self, fmt='', **kwargs):
        """Plot the data over the current figure."""
        self.plot(fmt=fmt, over=True, **kwargs)

    def logplot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
                vmin=None, vmax=None, **kwargs):
        """Plot the data intensity on a log scale."""
        self.plot(fmt=fmt, log=True,
                  xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                  vmin=vmin, vmax=vmax, **kwargs)

    def implot(self, fmt='', xmin=None, xmax=None, ymin=None, ymax=None,
                vmin=None, vmax=None, **kwargs):
        """Plot the data intensity as an RGB(A) image."""
        if (self.nxsignal.plot_rank > 2 and 
            (self.nxsignal.shape[-1] == 3 or self.nxsignal.shape[-1] == 4)):
            self.plot(fmt=fmt, image=True,
                      xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                      vmin=vmin, vmax=vmax, **kwargs)
        else:
            raise NeXusError("Invalid shape for RGB(A) image")

    @property
    def ndim(self):
        """Rank of the NXdata signal."""
        signal = self.nxsignal
        if signal is not None:
            return signal.ndim
        else:
            raise NeXusError("No signal defined for NXdata group")

    @property
    def shape(self):
        """Shape of the NXdata signal."""
        signal = self.nxsignal
        if signal is not None:
            return signal.shape
        else:
            raise NeXusError("No signal defined for NXdata group")

    @property
    def nxsignal(self):
        """NXfield containing the signal data."""
        if 'signal' in self.attrs and self.attrs['signal'] in self:
            return self[self.attrs['signal']]
        for obj in self.values():
            if 'signal' in obj.attrs and text(obj.attrs['signal']) == '1':
                if isinstance(self[obj.nxname], NXlink):
                    return self[obj.nxname].nxlink
                else:
                    return self[obj.nxname]
        return None
    
    @nxsignal.setter
    def nxsignal(self, signal):
        current_signal = self.nxsignal
        if current_signal is not None and current_signal is not signal:
            if 'signal' in current_signal.attrs:
                del current_signal.attrs['signal']
        self.attrs['signal'] = signal.nxname
        if signal not in self:
            self[signal.nxname] = signal

    @property
    def nxaxes(self):
        """List of NXfields containing the axes."""
        def empty_axis(i):
            return NXfield(np.arange(self.nxsignal.shape[i]), name='Axis%s'%i)
        def plot_axis(axis):
            return NXfield(axis.nxvalue, name=axis.nxname, attrs=axis.attrs) 
        try:
            if 'axes' in self.attrs:
                axis_names = _readaxes(self.attrs['axes'])
            elif self.nxsignal is not None and 'axes' in self.nxsignal.attrs:
                axis_names = _readaxes(self.nxsignal.attrs['axes'])
            axes = [None] * len(axis_names)
            for i, axis_name in enumerate(axis_names):
                axis_name = axis_name.strip()
                if axis_name == '' or axis_name == '.':
                    axes[i] = empty_axis(i)
                else:
                    axes[i] = plot_axis(self[axis_name])
            return axes
        except (AttributeError, IndexError, KeyError, UnboundLocalError):
            axes = {}
            for entry in self:
                if 'axis' in self[entry].attrs:
                    axis = self[entry].attrs['axis']
                    if axis not in axes and self[entry] is not self.nxsignal:
                        axes[axis] = self[entry]
                    else:
                        return None
            if axes:
                return [plot_axis(axes[axis]) for axis in sorted(axes)]
            elif self.nxsignal is not None:
                return [NXfield(np.arange(self.nxsignal.shape[i]), 
                        name='Axis%s'%i) for i in range(self.nxsignal.ndim)]
            return None

    @nxaxes.setter
    def nxaxes(self, axes):
        if not is_iterable(axes):
            axes = [axes]
        axes_attr = []
        for axis in axes:
            if axis is None:
                axes_attr.append('.')
            else:
                axes_attr.append(axis.nxname)
                if axis not in self:
                    self[axis.nxname] = axis
        self.attrs['axes'] = axes_attr

    @property
    def nxerrors(self):
        """NXfield containing the signal errors."""
        if self.nxsignal is not None: 
            if ('uncertainties' in self.nxsignal.attrs and
                self.nxsignal.attrs['uncertainties'] in self):
                return self[self.nxsignal.attrs['uncertainties']]
            elif self.nxsignal.nxname+'_errors' in self:
                return self[self.nxsignal.nxname+'_errors']
        try:
            return self['errors']
        except KeyError:
            return None

    @nxerrors.setter
    def nxerrors(self, errors):
        if self.nxsignal is not None:
            name = self.nxsignal.nxname+'_errors'
            self.nxsignal.attrs['uncertainties'] = name
        else:
            name = 'errors'
        self[name] = errors
        return self.entries[name]

    @property
    def mask(self):
        """NXfield containing the signal mask if one exists.
        
        This is set to a value of None or np.ma.nomask to remove the mask.
        """
        if self.nxsignal is not None:
            return self.nxsignal.mask
        else:
            return None

    @mask.setter
    def mask(self, value):
        if value is None:
            value = np.ma.nomask
        if value is np.ma.nomask and self.nxsignal.mask is not None:
            self.nxsignal.mask = np.ma.nomask
            if isinstance(self.nxsignal.mask, NXfield):
                del self[self.nxsignal.mask.nxname]
            if 'mask' in self.nxsignal.attrs:
                del self.nxsignal.attrs['mask']


class NXmonitor(NXdata):
    """NXmonitor group, a subclass of the NXdata class."""

    def __init__(self, signal=None, axes=None, *args, **kwargs):
        NXdata.__init__(self, signal=signal, axes=axes, *args, **kwargs)
        self._class = "NXmonitor"
        if "name" not in kwargs:
            self._name = "monitor"


class NXlog(NXgroup):
    """NXlog group, a subclass of the NXgroup class."""

    def __init__(self, *args, **kwargs):
        self._class = "NXlog"
        NXgroup.__init__(self, *args, **kwargs)

    def plot(self, **kwargs):
        """Plot the logged values against the elapsed time. 
        
        Valid Matplotlib parameters, specifying markers, colors, etc, can be 
        specified using the 'kwargs' dictionary.
        """
        title = NXfield("%s Log" % self.nxname)
        if 'start' in self['time'].attrs:
            title = title + ' - starting at ' + self['time'].attrs['start']
        NXdata(self['value'], self['time'], title=title).plot(**kwargs)


class NXprocess(NXgroup):
    """NXprocess group, a subclass of the NXgroup class."""

    def __init__(self, *args, **kwargs):
        self._class = "NXprocess"
        NXgroup.__init__(self, *args, **kwargs)
        if "date" not in self:
            from datetime import datetime as dt
            self.date = dt.isoformat(dt.today())


class NXnote(NXgroup):
    """NXnote group, a subclass of the NXgroup class."""

    def __init__(self, *args, **kwargs):
        self._class = "NXnote"
        NXgroup.__init__(self, **kwargs)
        for arg in args:
            if is_text(arg):
                if "description" not in self:
                    self.description = arg
                elif "data" not in self:
                    self.data = arg
            elif isinstance(arg, NXobject):
                setattr(self, arg.nxname, arg)
            else:
                raise NeXusError(
                    "Non-keyword arguments must be valid NXobjects")
        if "date" not in self:
            from datetime import datetime as dt
            self.date = dt.isoformat(dt.today())


#-------------------------------------------------------------------------
#Add remaining base classes as subclasses of NXgroup and append to __all__

for cls in nxclasses:
    if cls not in globals():
        globals()[cls] = _makeclass(cls)
    __all__.append(cls)

#-------------------------------------------------------------------------
def is_real_slice(idx):
    """True if the slice contains real values."""

    def is_real(x):
        if isinstance(x, slice):
            x = [x if x is not None else 0 for x in [x.start, x.stop, x.step]]
        x = np.array(x)
        return not (np.issubdtype(x.dtype, np.integer) or x.dtype == np.bool)

    if isinstance(idx, slice):
        return is_real(idx)
    elif is_iterable(idx):
        return any([is_real(i) for i in idx])
    else:
        return is_real(idx)

def convert_index(idx, axis):
    """Convert floating point limits to a valid array index.

    This is for one-dimensional axes only. If the index is a tuple of slices, 
    i.e., for two or more dimensional data, the index is returned unchanged.
    
    Parameters
    ----------
    idx : slice
        Slice to be converted.
    axis : NXfield
        Axis used to define the indices of the float values.
    
    Returns
    -------
    slice
        Converted slice.    
    """
    if is_real_slice(idx) and axis.ndim > 1: 
        raise NeXusError(
            "NXfield must be one-dimensional for floating point slices")
    elif is_iterable(idx) and len(idx) > axis.ndim:
        raise NeXusError("Slice dimension incompatible with NXfield")
    if axis.size == 1:
        idx = 0
    elif isinstance(idx, slice) and not is_real_slice(idx):
        if idx.start is not None and idx.stop is not None:
            if idx.stop == idx.start or idx.stop == idx.start + 1:
                idx = idx.start
    elif isinstance(idx, slice):
        if isinstance(idx.start, NXfield) and isinstance(idx.stop, NXfield):
            idx = slice(idx.start.nxdata, idx.stop.nxdata, idx.step)
        if (idx.start is not None and idx.stop is not None and
            ((axis.reversed and idx.start < idx.stop) or
             (not axis.reversed and idx.start > idx.stop))):
            idx = slice(idx.stop, idx.start, idx.step)
        if idx.start is None:
            start = None
        else:
            start = axis.index(idx.start)
        if idx.stop is None:
            stop = None
        else:
            stop = axis.index(idx.stop, max=True) + 1
        if start is None or stop is None:
            idx = slice(start, stop, idx.step)
        elif stop <= start+1 or np.isclose(idx.start, idx.stop):
            idx = start
        else:
            idx = slice(start, stop, idx.step)
    elif (not isinstance(idx, numbers.Integral) and
             isinstance(idx, numbers.Real)):
        idx = axis.index(idx)
    return idx

def centers(axis, dimlen):
    """Return the centers of the axis bins.

    This works regardless if the axis contains bin boundaries or 
    centers.
    
    Parameters
    ----------
    dimlen : int
        Size of the signal dimension. If this is one more than the axis 
        size, it is assumed the axis contains bin boundaries.
    """
    ax = axis.astype(np.float64)
    if ax.shape[0] == dimlen+1:
        return (ax[:-1] + ax[1:])/2
    else:
        assert ax.shape[0] == dimlen
        return ax

def getlock():
    """Return the number of seconds before a lock acquisition times out.

    If the value is 0, file locking is disabled.
    
    Returns
    -------
    int
        Number of seconds before a lock acquisition times out.
    """
    return NX_LOCK
    
def setlock(value=10):
    """Initialize NeXus file locking.

    This creates a file with `.lock` appended to the NeXus file name.
    
    Parameters
    ----------
    value : int, optional
        Number of seconds before a lock acquisition times out, by default 10.
        If the value is set to 0, file locking is disabled.
    """
    global NX_LOCK
    NX_LOCK = int(value)

nxgetlock = getlock
nxsetlock = setlock

def getmemory():
    """Return the memory limit for data arrays (in MB)."""
    return NX_MEMORY

def setmemory(value):
    """Set the memory limit for data arrays (in MB)."""
    global NX_MEMORY
    NX_MEMORY = value

nxgetmemory = getmemory
nxsetmemory = setmemory

def getcompression():
    """Return default compression filter."""
    return NX_COMPRESSION

def setcompression(value):
    """Set default compression filter."""
    global NX_COMPRESSION
    if value == 'None':
        value = None
    NX_COMPRESSION = value

nxgetcompression = getcompression
nxsetcompression = setcompression

def getencoding():
    """Return the default encoding for input strings (usually 'utf-8')."""
    return NX_ENCODING

def setencoding(value):
    """Set the default encoding for input strings (usually 'utf-8')."""
    global NX_ENCODING
    NX_ENCODING = value

nxgetencoding = getencoding
nxsetencoding = setencoding

def getmaxsize():
    """Return the default maximum size for arrays without using core memory."""
    return NX_MAXSIZE

def setmaxsize(value):
    """Set the default maximum size for arrays without using core memory."""
    global NX_MAXSIZE
    NX_MAXSIZE = value

nxgetmaxsize = getmaxsize
nxsetmaxsize = setmaxsize

# File level operations
def load(filename, mode='r', **kwargs):
    """Open or create a NeXus file and load its tree.
    
    Notes
    -----
    This is aliased to `nxload` to avoid name clashes with other packages,
    such as Numpy. `nxload` is the version included in wild card imports.
    
    Parameters
    ----------
    filename : str
        Name of the file to be opened or created.
    mode : {'r', 'rw', 'r+', 'w', 'a'}, optional
        File mode, by default 'r'
    
    Returns
    -------
    NXroot
        NXroot object containing the NeXus tree.
    """
    with NXFile(filename, mode, **kwargs) as f:
        root = f.readfile()
    return root

nxload = load

def save(filename, group, mode='w', **kwargs):
    """Write a NeXus file from a tree of NeXus objects.
    
    Parameters
    ----------
    filename : str
        Name of the file to be saved.
    group : NXgroup
        Group containing the tree to be saved.
    mode : {'w', 'w-', 'a'}, optional
        Mode to be used opening the file, by default 'w'.
    """
    if group.nxclass == "NXroot":
        root = group
    elif group.nxclass == "NXentry":
        root = NXroot(group)
    else:
        root = NXroot(NXentry(group))
    with NXFile(filename, mode, **kwargs) as f:
        f.writefile(root)
        f.close()
 
nxsave = save

def duplicate(input_file, output_file, mode='w-', **kwargs):
    """Duplicate an existing NeXus file.
    
    Parameters
    ----------
    input_file : str
        Name of file to be copied.
    output_file : str
        Name of the new file.
    mode : {'w', 'w-', 'a'}, optional
        Mode to be used in opening the new file, by default 'w-'.
    """
    with NXFile(input_file, 'r') as input, NXFile(output_file, mode) as output:
        output.copyfile(input, **kwargs)

nxduplicate = duplicate

def directory(filename):
    """Print the contents of the named NeXus file.
    
    Parameters
    ----------
    filename : str
        Name of the file to be read.
    """
    root = load(filename)
    print(root.tree)

nxdir = directory


def demo(argv):
    """Process a list of command line commands.
    
    Parameters
    ----------
    argv : list of str
        List of commands.
    """
    if len(argv) > 1:
        op = argv[1]
    else:
        op = 'help'
    if op == 'ls':
        for f in argv[2:]: dir(f)
    elif op == 'copy' and len(argv)==4:
        tree = load(argv[2])
        save(argv[3], tree)
    elif op == 'plot' and len(argv)==4:
        tree = load(argv[2])
        for entry in argv[3].split('.'):
            tree = getattr(tree,entry)
        tree.plot()
        tree._plotter.show()

    else:
        usage = """
    usage: %s cmd [args]
    copy fromfile.nxs tofile.nxs
    ls *.nxs
    plot file.nxs entry.data
        """%(argv[0],)
        print(usage)

nxdemo = demo


if __name__ == "__main__":
    import sys
    nxdemo(sys.argv)
