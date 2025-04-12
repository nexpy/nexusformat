#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Copyright (c) 2024-2025, Kaitlyn Marlor, Ray Osborn, Justin Wozniak.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------

import argparse

import nexusformat
from nexusformat.nexus.validate import inspect_base_class


def main():
    parser = argparse.ArgumentParser(
        prog="nxinspect",
        description="Inspects base classes.")
    parser.add_argument('baseclass', action='store', nargs=1,
        help='base class to be inspected')
    parser.add_argument("-d", "--definitions", nargs = 1,
        help = "path to the directory containing NeXus definitions")
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s v'+nexusformat.__version__)
    args = parser.parse_args()

    if args.definitions:
        definitions = args.definitions[0]
    else:
        definitions = None

    if args.baseclass:
        baseclass = args.baseclass[0]
        inspect_base_class(baseclass, definitions=definitions)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
