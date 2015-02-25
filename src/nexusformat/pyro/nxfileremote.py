
"""
NXFileRemote
The wrapper class representing a remote NX file
Contains a Pyro proxy
"""

import os
import sys
import Pyro4

from nexusformat.nexus import NXFile

import numpy as np

def message(msg):
    print("pyro client: " + str(msg))

class NXFileRemote(NXFile):

    def __init__(self, name, uri):
        # Get a Pyro proxy to the remote object
        Pyro4.config.SERIALIZER = "pickle"
        message("proxy connect")
        proxy = Pyro4.Proxy(uri)
        message("proxy init")
        proxy._pyroTimeout = 20.0
        b = proxy.initfile(name)
        if b != True:
            print "\nERROR OCCURRED IN SERVICE"
            print b
            return
        message("file init")
        self._mode = 'r'
        self._file = proxy
        self._filename = name
        assert(b)

    def __repr__(self):
        return '<NXFileRemote "%s" (mode %s)>' % (os.path.basename(self._filename),
                                                  self._mode)

    def __getitem__(self, key):
        return self._file.getitem(key)

    def __setitem__(self, key, value):
        return self._file.setitem(key, value)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def open(self, **kwds):
        return self

    def close(self):
        pass

    def get(self, key):
        return self._file.getitem(key)

    def readvalue(self, path, idx=()):
        return self._file.getvalue(path, idx=idx)

    def writevalue(self, path, value, idx=()):
        return self._file.setvalue(path, value, idx=idx)

    def readfile(self):
        tree = self._file.tree()
        tree._file = self
        tree._filename = self._filename
        return tree
        

def nxloadremote(filename, uri):
    """
    Reads a NeXus file returning a tree of objects.

    This is aliased to 'nxload' because of potential name clashes with Numpy
    """
    with NXFileRemote(filename, uri) as run:
        tree = run.readfile()
        print tree.__class__
    return tree


