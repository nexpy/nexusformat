#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Copyright (c) 2013-2014, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
#-----------------------------------------------------------------------------

from setuptools import setup, find_packages, Extension

import os, sys
import pkg_resources
pkg_resources.require('numpy')
import numpy

# pull in some definitions from the package's __init__.py file
sys.path.insert(0, os.path.join('src', ))
import nexpyro
import nexpyro.requires

verbose=1

setup (name =  nexpyro.__package_name__,        # NeXpy
       version = nexpyro.__version__,
       license = nexpyro.__license__,
       description = nexpyro.__description__,
       long_description = nexpyro.__long_description__,
       author=nexpyro.__author_name__,
       author_email=nexpyro.__author_email__,
       url=nexpyro.__url__,
       download_url=nexpyro.__download_url__,
       platforms='any',
       install_requires = nexpyro.requires.pkg_requirements,
       package_dir = {'': 'src'},
       packages = find_packages('src'),
       entry_points={
            'command_line_scripts': ['nxstartserver = nexpyro.start_server:main',],
       },
       classifiers= ['Development Status :: 4 - Beta',
                     'Intended Audience :: Developers',
                     'Intended Audience :: Science/Research',
                     'License :: OSI Approved :: BSD License',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 2',
                     'Programming Language :: Python :: 2.7',
                     'Topic :: Scientific/Engineering',
                     'Topic :: Scientific/Engineering :: Visualization'],
      )
