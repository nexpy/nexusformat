#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Copyright (c) 2019-2021, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------
import argparse

import nexusformat


def main():

    parser = argparse.ArgumentParser(
        description="Determine version number of nexusformat API")
    parser.add_argument('-v', '--version', action='version',
                        version=f'nexusformat v{nexusformat.__version__}')

    parser.parse_args(['--version'])


if __name__ == "__main__":
    main()
