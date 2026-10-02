#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Copyright (c) 2025-2026, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------

import argparse
import logging

import nexusformat
from nexusformat.nexus.validate import lint_nxdl, log, log_summary, logger


def main():
    parser = argparse.ArgumentParser(
        prog="nxlint",
        description="Check NXDL application definition files for structural "
                    "errors.")
    parser.add_argument("filename", nargs='+',
        help="NXDL file(s) to lint")
    parser.add_argument("-d", "--definitions", nargs=1,
        help="path to the directory containing NeXus definitions")
    parser.add_argument("-i", "--info", action='store_true',
        help="output info messages in addition to warnings and errors")
    parser.add_argument("-w", "--warning", action='store_true',
        help="output warning and error messages (default)")
    parser.add_argument("-e", "--error", action='store_true',
        help="output errors only")
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

    for filename in args.filename:
        log("\n", level='all')
        log(f"NXDL file: {filename}", level='all')
        if definitions:
            log(f"Definitions: {definitions}", level='all')
        log("\n", level='all')
        logger.total = {'warning': 0, 'error': 0}

        results = lint_nxdl(filename, definitions=definitions)
        if results:
            for message, location, severity in results:
                log(f'[{location}] {message}', level=severity)
            log('\nFor help interpreting these errors, consult the NXDL '
                'reference at https://manual.nexusformat.org/nxdl.html',
                level='all')
        else:
            log(f'No structural errors found in "{filename}"', level='all')

        log_summary()


if __name__ == "__main__":
    main()
