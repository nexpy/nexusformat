
"""
NXFileRemote
The wrapper class representing a remote NX file
Contains a Pyro proxy
"""

import sys
import Pyro4

import nexpy.api.nexus as nx
from nexpy.api.nexus import NXFile

import numpy as np

def message(msg):
    print("pyro client: " + str(msg))

class NXFileRemote(NXFile):

    def __init__(self, uri, name):
        # Get a Pyro proxy to the remote object
        Pyro4.config.SERIALIZER = "pickle"
        message("proxy connect")
        proxy = Pyro4.Proxy(uri)
        message("proxy init")
        b = proxy.initfile(name)
        if b != True:
            print "\nERROR OCCURRED IN SERVICE"
            print b
            return
        message("file init")
        NXFile.__init__(self, name, proxy=proxy)
        assert(b)

    def __getitem__(self, key):
        return self._file.getitem(key)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._file.exit(0)
