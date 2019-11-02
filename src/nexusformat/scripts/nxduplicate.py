#!/usr/bin/env python
#-----------------------------------------------------------------------------
# Copyright (c) 2019, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
#-----------------------------------------------------------------------------
from __future__ import (division, print_function)

import argparse
from nexusformat.nexus import *
from nexusformat import __version__

def main():

    parser = argparse.ArgumentParser(
        description="Copy a NeXus file to another file")
    parser.add_argument('input', action='store', 
                        help="name of NeXus input file")
    parser.add_argument('output', action='store', 
                        help="name of NeXus output file")
    parser.add_argument('-e', '--expand_external',action='store_true',
                        help="store external links within the new file")
    parser.add_argument('-o', '--overwrite',action='store_true',
                        help="overwrite any existing file")
    parser.add_argument('-v', '--version', action='version', 
                        version='nxduplicate v%s' % __version__)

    args = parser.parse_args()

    if args.overwrite:
        mode = 'w'
    else:
        mode = 'w-'
    nxduplicate(args.input, args.output, mode=mode, 
                expand_external=args.expand_external)


if __name__ == "__main__":
    main()
