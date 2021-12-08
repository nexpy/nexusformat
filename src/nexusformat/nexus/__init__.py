# -----------------------------------------------------------------------------
# Copyright (c) 2013-2021, NeXpy Development Team.
#
# Author: Paul Kienzle, Ray Osborn
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------

"""
Python NeXus interface.

NeXus is a common data format for neutron, Xray and muon science.
The files contain multidimensional data elements grouped into a
hierarchical structure.  The data sets are self-describing, with
a description of the instrument configuration including the units
used as well as the data measured. NeXus data are written to HDF
files and accessed in this package using h5py.

Example
=======

First we need to load the file structure::

    import nexusformat.nexus as nx
    f = nx.load('file.nxs')

We can examine the file structure using a number of commands::

    f.attrs             # Shows file name, date, user, and NeXus version
    print(f.tree)       # Lists the entire contents of the NeXus file
    f.NXentry           # Shows the list of scans in the file
    f.NXentry[0].dir()  # Lists the fields in the first entry

Some files can even be plotted automatically::

    f.NXentry[0].NXdata[0].plot()


For a complete description of the features available in this tree view
of the NeXus data file, see `nx.tree`.
"""
from .completer import nxcompleter
from .lock import NXLock, NXLockException
from .tree import *
