#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Copyright (c) 2019-2021, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------
import argparse

from nexusformat import __version__
from nexusformat.nexus import nxdir


def main():

    parser = argparse.ArgumentParser(
        description="Print a NeXus file tree")
    parser.add_argument('file', action='store', help="name of NeXus file")
    parser.add_argument('-s', '--short', action='store_true',
                        help="print only the first level")
    parser.add_argument('-v', '--version', action='version',
                        version=f'nxdir v{__version__}')

    args = parser.parse_args()

    nxdir(args.file, short=args.short)


if __name__ == "__main__":
    main()
