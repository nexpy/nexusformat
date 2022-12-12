#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Copyright (c) 2013-2022, NeXpy Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------
import argparse
import re
import socket
import sys
import timeit
from pathlib import Path

import numpy as np

from nexusformat.nexus import (NeXusError, NXdata, NXentry, NXfield, NXnote,
                               NXprocess, NXroot, nxsetcompression, nxversion)

prefix_pattern = re.compile(r'^([^.]+)(?:(?<!\d)|(?=_))')
index_pattern = re.compile(r'^(.*?)([0-9]*)[.](.*)$')


def natural_sort(key):
    import re
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', key)]


def get_prefixes(directory):
    prefixes = []
    for filename in Path(directory).iterdir():
        match = prefix_pattern.match(filename.stem)
        if match:
            prefixes.append(match.group(1).strip('-').strip('_'))
    return list(set(prefixes))


def get_files(directory, prefix, extension, first=None, last=None,
              reverse=False):
    if not extension.startswith('.'):
        extension = '.' + extension
    filenames = sorted(
        [str(f) for f in Path(directory).glob(prefix+'*'+extension)],
        key=natural_sort, reverse=reverse)
    if len(filenames) == 0:
        print("No filenames matched!")
        exit(0)
    max_index = get_index(filenames[-1])
    if first:
        min_index = first
    else:
        min_index = get_index(filenames[0])
    if last:
        max_index = last
    else:
        max_index = get_index(filenames[-1])
    return [filename for filename in filenames if
            min_index <= get_index(filename) <= max_index]


def get_index(filename):
    return int(index_pattern.match(str(filename)).group(2))


def read_image(filename):
    try:
        import fabio
    except ImportError:
        raise NeXusError("Please install the 'fabio' module")
    im = fabio.open(str(filename))
    return im.data


def read_images(filenames, shape):
    good_files = [str(f) for f in filenames if f is not None]
    if good_files:
        v0 = read_image(good_files[0])
        if v0.shape != shape:
            raise AssertionError(
                f'Image shape of {good_files[0]} not consistent')
        v = np.empty([len(filenames), v0.shape[0], v0.shape[1]],
                     dtype=np.float32)
    else:
        v = np.empty([len(filenames), shape[0], shape[1]], dtype=np.float32)
    v.fill(np.nan)
    for i, filename in enumerate(filenames):
        if filename:
            v[i] = read_image(filename)
    return v


def initialize_nexus_file(output_file, filenames, first):
    z_size = get_index(filenames[-1]) - get_index(filenames[0]) + 1
    v0 = read_image(filenames[0])
    x = NXfield(range(v0.shape[1]), dtype=np.uint16, name='x_pixel')
    y = NXfield(range(v0.shape[0]), dtype=np.uint16, name='y_pixel')
    if z_size > 1:
        z = first + np.arange(z_size)
        z = NXfield(z, dtype=np.uint16, name='frame_number', maxshape=(5000,))
        v = NXfield(name='data', shape=(z_size, v0.shape[0], v0.shape[1]),
                    dtype=np.float32,
                    maxshape=(5000, v0.shape[0], v0.shape[1]))
        data = NXdata(v, (z, y, x))
    else:
        v = NXfield(name='data', shape=(v0.shape[0], v0.shape[1]),
                    dtype=np.float32)
        data = NXdata(v, (y, x))
    root = NXroot(NXentry(data))
    root.save(output_file, 'w')
    return root


def write_data(root, filenames):
    if len(root.entry.data.data.shape) == 2:
        root.entry.data.data[:, :] = read_image(filenames[0])
    else:
        z_size = root.entry.data.data.shape[0]
        image_shape = root.entry.data.data.shape[1:3]
        chunk_size = root.entry.data.data.chunks[0]
        min_index = get_index(filenames[0])
        max_index = get_index(filenames[-1])
        k = 0
        for i in range(min_index, min_index+z_size, chunk_size):
            files = []
            for j in range(i, min(i+chunk_size, max_index+1)):
                if j == get_index(filenames[k]):
                    print('Processing', filenames[k])
                    files.append(filenames[k])
                    k += 1
                elif k < len(filenames):
                    files.append(None)
                else:
                    break
            root.entry.data.data[i-min_index:i+len(files)-min_index, :, :] = (
                read_images(files, image_shape))


def main():

    parser = argparse.ArgumentParser(
        description="Stack images into a single NeXus file")
    parser.add_argument('-d', '--directory', default=Path.cwd(),
                        help="directory containing the raw images")
    parser.add_argument('-p', '--prefix', nargs='+',
                        help="common prefix to all images")
    parser.add_argument('-e', '--extension', default='.tif',
                        help="file extension of raw images")
    parser.add_argument('-o', '--output', help="name of NeXus output file")
    parser.add_argument('-f', '--first', default=0, type=int,
                        help="first frame to be included in the stacked data")
    parser.add_argument('-l', '--last', type=int,
                        help="last frame to be included in the stacked data")
    parser.add_argument('-r', '--reverse', action='store_true',
                        help="store images in reverse order")
    parser.add_argument('-c', '--compression', help="HDF5 compression method")
    parser.add_argument('-v', '--version', action='version',
                        version=f'nxstack v{nxversion}')

    args = parser.parse_args()
    directory = Path(args.directory)
    extension = args.extension
    if not extension.startswith('.'):
        extension = '.' + extension
    if args.output is not None:
        output = Path(args.output)
        if output.suffix == '':
            output = output.with_suffix('.nxs')
    else:
        output = None

    compression = args.compression
    if compression:
        nxsetcompression(compression)

    first = args.first
    last = args.last
    reverse = args.reverse

    if args.prefix is None:
        prefixes = get_prefixes(directory)
        if len(prefixes) > 1 and output is not None:
            raise NeXusError(
                "Only one prefix allowed if the output file is specified")
    else:
        prefixes = args.prefix

    for prefix in prefixes:
        tic = timeit.default_timer()
        data_files = get_files(directory, prefix, extension, first, last,
                               reverse)
        if output is None:
            output_file = Path(prefix + '.nxs')
        else:
            output_file = output
        root = initialize_nexus_file(output_file, data_files, first)
        write_data(root, data_files)
        note = NXnote('nxstack '+' '.join(sys.argv[1:]),
                      (f'Current machine: {socket.gethostname()}\n'
                       f'Current working directory: {Path.cwd()}\n'
                       f'Data files: {data_files[0]} to {data_files[-1]}\n'))
        root.entry['nxstack'] = NXprocess(
            program='nxstack', sequence_index=len(root.entry.NXprocess) + 1,
            version=nxversion, note=note)

        toc = timeit.default_timer()
        print(toc-tic, 'seconds for', output_file)


if __name__ == "__main__":
    main()
