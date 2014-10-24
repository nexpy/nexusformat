Installation
============
Released versions of NeXpy-RO are available on `PyPI 
<https://pypi.python.org/pypi/NeXpy-RO/>`_. If you have the `Python Setup Tools 
<https://pypi.python.org/pypi/setuptools>`_ installed, then you can install 
using either::

    $ pip install nexpyro

or:: 

    $ easy_install nexpyro 

If you have trouble with the pip or easy_install installations, you can install
the package from the source code either by downloading one of the 
`Github releases <https://github.com/nexpy/nexpy/releases>`_ or by cloning the
latest development version in the `NeXpy Git 
repository <https://github.com/nexpy/nexpyro>`_::

    $ git clone http://github.com/nexpy/nexpyro.git

You can then install NeXpy by changing to the source directory and typing::

    $ python setup.py install

To install in an alternate location::

    $ python setup.py install --prefix=/path/to/installation/dir

Required Libraries
==================

=================  =================================================
Library            URL
=================  =================================================
h5py               http://www.h5py.org
numpy              http://numpy.scipy.org/
pyro4              http://pythonhosted.org//Pyro4/
=================  =================================================

Semantic Versioning
-------------------
NeXpy-RO is using `Semantic Versioning <http://semver.org/spec/v2.0.0.html>`_.

User Support
------------
Consult the `NeXpy documentation <http://nexpy.github.io/nexpy/>`_ for details 
of both NeXpy and NeXpy-RO. If you have any general questions concerning the use 
of NeXpy, please address them to the `NeXus Mailing List 
<http://download.nexusformat.org/doc/html/mailinglist.html>`_. If you discover
any bugs, please submit a `Github issue 
<https://github.com/nexpy/nexpyro/issues>`_, preferably with relevant 
tracebacks.

Acknowledgements
----------------
The `NeXus format <http://www.nexusformat.org>`_ for neutron, x-ray and muon 
data is developed by an international collaboration under the supervision of the 
`NeXus International Advisory Committee <http://wiki.nexusformat.org/NIAC>`_. 
The Python tree API used in NeXpy was originally developed by Paul Kienzle, who
also wrote the standard Python interface to the NeXus C-API. The original 
version of NeXpy was initially developed by Boyana Norris, Jason Sarich, and 
Daniel Lowell, and Ray Osborn using wxPython, and formed the inspiration
for the current PySide version.
