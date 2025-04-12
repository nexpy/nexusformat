#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Copyright (c) 2024-2025, Kaitlyn Marlor, Ray Osborn, Justin Wozniak.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------

import argparse
import logging

import nexusformat
from nexusformat.nexus.validate import (logger, validate_application,
                                        validate_file)


def main():
    parser = argparse.ArgumentParser(
        prog="nxcheck",
        description="Check NeXus files against the NeXus standard.")
    parser.add_argument("filename", nargs = 1,
        help="name of the NeXus file to be validated")
    parser.add_argument("-p", "--path", nargs = 1,
        help = "path to group to be validated in the NeXus file")
    parser.add_argument("-a", "--application", nargs='?', const=True,
        help = "validate the NeXus file against its application definition")
    parser.add_argument("-d", "--definitions", nargs = 1,
        help = "path to the directory containing NeXus definitions")
    parser.add_argument("-i", "--info", action='store_true',
        help = "output info messages in addition to warnings and errors")
    parser.add_argument("-w", "--warning", action='store_true',
        help = "output warning and error messages (default)")
    parser.add_argument("-e", "--error", action='store_true',
        help = "output errors")
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s v'+nexusformat.__version__)
    args = parser.parse_args()

    if args.info:
        logger.setLevel(logging.INFO)
    elif args.warning:
        logger.setLevel(logging.WARNING)
    elif args.error:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.WARNING)

    if args.definitions:
        definitions = args.definitions[0]
    else:
        definitions = None

    if args.filename:
        filename = args.filename[0]
        if args.path:
            path = args.path[0]
        else:
            path = None
        if args.application:
            if args.application is True:
                application = None
            else:
                application = args.application
            validate_application(filename, path=path, application=application,
                                 definitions=definitions)
        else:
            validate_file(filename, path=path, definitions=definitions)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
