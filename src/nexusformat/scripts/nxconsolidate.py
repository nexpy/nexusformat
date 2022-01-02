#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Copyright (c) 2019-2022, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------
import argparse

from nexusformat import __version__
from nexusformat.nexus import NXentry, NXroot, nxconsolidate


def main():

    parser = argparse.ArgumentParser(
        description="Copy a NeXus file to another file")
    parser.add_argument('files', action='store', nargs='*',
                        help="name of NeXus input files (wild cards allowed)")
    parser.add_argument('-d', '--data', required=True,
                        help="path to the NXdata group")
    parser.add_argument('-s', '--scan', help="path to the scan variable")
    parser.add_argument('-e', '--entry', default='entry',
                        help="name of NXentry group")
    parser.add_argument('-o', '--output', required=True,
                        help="name of NeXus output file")
    parser.add_argument('-v', '--version', action='version',
                        version=f'nxconsolidate v{__version__}')

    args = parser.parse_args()

    scan_data = nxconsolidate(args.files, args.data, scan_path=args.scan)
    NXroot(NXentry(scan_data, name=args.entry)).save(args.output, 'w-')


if __name__ == "__main__":
    main()
