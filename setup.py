#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Copyright (c) 2013-2016, NeXpy Development Team.
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
import versioneer

# pull in some definitions from the package's __init__.py file
sys.path.insert(0, os.path.join('src', ))
import nexusformat
import nexusformat.requires

verbose=1

setup (name =  nexusformat.__package_name__, # NeXpy
       version=versioneer.get_version(),
       cmdclass=versioneer.get_cmdclass(),
       license = nexusformat.__license__,
       description = nexusformat.__description__,
       long_description = nexusformat.__long_description__,
       author=nexusformat.__author_name__,
       author_email=nexusformat.__author_email__,
       url=nexusformat.__url__,
       download_url=nexusformat.__download_url__,
       platforms='any',
       install_requires = nexusformat.requires.pkg_requirements,
       package_dir = {'': 'src'},
       packages = find_packages('src'),
       entry_points={
            # create & install scripts in <python>/bin
            'console_scripts': ['nxstack=nexusformat.scripts.nxstack:main'],
       },
       classifiers= ['Development Status :: 4 - Beta',
                     'Intended Audience :: Developers',
                     'Intended Audience :: Science/Research',
                     'License :: OSI Approved :: BSD License',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 2',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3',
                     'Programming Language :: Python :: 3.3',
                     'Programming Language :: Python :: 3.4',
                     'Programming Language :: Python :: 3.5',
                     'Topic :: Scientific/Engineering',
                     'Topic :: Scientific/Engineering :: Visualization'],
      )
