
"""
NXFileRemote
The wrapper class representing a remote NX file
Contains a Pyro proxy
"""

import sys
import Pyro4

import nexpyro.nexus as nx
from nexpyro.nexus import NXFile
from nexpy.api.nexus import NXfield

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
        NXFile.__init__(self, name, proxy=proxy)
        assert(b)

    def __getitem__(self, key):
        return self._file.getitem(key)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._file.exit(0)

    def _readvalue(self, path, key=None):
        return self._file.getvalue(path, key)

    def readfile(self):
        tree = self._file.tree()
        tree._file = self
        return tree
        

def setserver(value):
    global _global_server
    _global_server = value
    
def getserver():
    global _global_server
    return _global_server 

def nxloadremote(filename, uri):
    """
    Reads a NeXus file returning a tree of objects.

    This is aliased to 'nxload' because of potential name clashes with Numpy
    """
    nxrfile = NXFileRemote(filename, uri)
    tree = nxrfile.readfile()
    print "nx.load done."
    return tree


