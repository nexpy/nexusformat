
"""
NXFileRemote
The wrapper class representing a remote NX file
Contains a Pyro proxy
"""

import os
import Pyro4

from nexusformat.nexus import NXFile

import numpy as np

def message(msg):
    print("pyro client: " + str(msg))

class NXFileRemote(NXFile):

    def __init__(self, name, uri, hostname=None):
        # Get a Pyro proxy to the remote object
        Pyro4.config.SERIALIZER = "pickle"
        message("proxy connect")
        proxy = Pyro4.Proxy(uri)
        message("proxy init")
        proxy._pyroTimeout = 20.0
        b = proxy.initfile(name)
        if b != True:
            print "\nERROR OCCURRED IN SERVICE"
            return
        message("file init")
        self._mode = 'r'
        self._file = proxy
        self._filename = name
        self.hostname = hostname
        assert(b)

    def __repr__(self):
        return '<NXFileRemote "%s" (mode %s)>' % (os.path.basename(self._filename),
                                                  self._mode)

    def __getitem__(self, key):
        return self._file.getitem(self._filename, key)

    def __setitem__(self, key, value):
        return self._file.setitem(self._filename, key, value)

    def __delitem__(self, key):
        self._file.delitem(self._filename, key)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def open(self, **kwds):
        return self

    def close(self):
        pass

    def get(self, key):
        return self._file.getitem(self._filename, key)

    def readvalue(self, path, idx=()):
        return self._file.getvalue(self._filename, path, idx=idx)

    def readvalues(self, attrs=None):
        return self._file.readvalues(self._filename, self.nxpath, attrs)

    def writevalue(self, path, value, idx=()):
        self._file.setvalue(self._filename, path, value, idx=idx)

    def update(self, item, path=None):
        if path is not None:
            self.nxpath = path
        else:
            self.nxpath = item.nxgroup.nxpath
        self._file.update(self._filename, item, path)

    def readfile(self):
        self.tree = self._file.tree(self._filename)
        self.tree._file = self
        self.tree._filename = self._filename
        return self.tree

    @property
    def filename(self):
        """File name on disk"""
        return self._filename

    def _getmode(self):
        return self._mode

    def _setmode(self, mode):
        if mode == 'rw' or mode == 'r+':
            self._mode = 'rw'
        else:
            self._mode = 'r'
        self._file.setmode(self._filename, self._mode)  

    mode = property(_getmode, _setmode, doc="Property: Read/write mode of remote file")

def nxloadremote(filename, uri, hostname=None):
    """
    Reads a NeXus file returning a tree of objects.

    This is aliased to 'nxload' because of potential name clashes with Numpy
    """
    with NXFileRemote(filename, uri, hostname=hostname) as f:
        tree = f.readfile()
    return tree


