#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Copyright (c) 2019-2020, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
#-----------------------------------------------------------------------------
import argparse
from nexusformat import __version__

def main():

    parser = argparse.ArgumentParser(
        description="Determine version number of nexusformat API")
    parser.add_argument('-v', '--version', action='version', 
                        version='nexusformat v%s' % __version__)

    parser.parse_args(['--version'])

if __name__ == "__main__":
    main()
