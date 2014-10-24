Introduction
============
NeXpy-RO provides remote access across a network to NeXus data. It is designed 
to work in conjunction with NeXpy.

Installing and Running
======================
Released versions of NeXpy-RO can be installed using either

```
    $ pip install nexpyro
```

or

```
    $ easy_install nexpyro
```

The source code can be downloaded from the NeXpy Git repository:

```
    $ git clone http://github.com/nexpy/nexpyro.git
```

To install in the standard Python location:

```
    $ python setup.py install
```

To install in an alternate location:

```
    $ python setup.py install --prefix=/path/to/installation/dir
```

Prerequisites
=============
The following libraries are used by the full installation of NeXpy. There is 
more details of the nature of these dependencies in the 
[NeXpy documentation](http://nexpy.github.io/nexpy).

* h5py                 http://www.h5py.org
* numpy,scipy          http://numpy.scipy.org
* pyro4                http://pythonhosted.org//Pyro4/

The following environment variable may need to be set
PYTHONPATH --> paths to numpy,scipy if installed in a nonstandard place

All of the above are included in the Enthought Python Distribution v7.3.

User Support
============
Consult the [NeXpy documentation](http://nexpy.github.io/nexpy) for details 
of both the Python command-line API and how to use the NeXpy GUI. If you have 
any general questions concerning the use of NeXpy, please address 
them to the 
[NeXus Mailing List](http://download.nexusformat.org/doc/html/mailinglist.html). 
If you discover any bugs, please submit a 
[Github issue](https://github.com/nexpy/nexpyro/issues), preferably with 
relevant tracebacks.
