#!/usr/bin/env python 
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
# Copyright (c) 2013, NeXpy Development Team.
#
# Author: Paul Kienzle, Ray Osborn
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
#-----------------------------------------------------------------------------

"""
This module provides a standard Matplotlib plotting option to the NeXus Python
API
"""
import numpy as np
from nexusformat.nexus import NXfield, NeXusError


def _fixaxes(signal, axes):
    """
    Remove length-one dimensions from plottable data
    """
    shape = list(signal.shape)
    while 1 in shape: shape.remove(1)
    newaxes = []
    for axis in axes:
        if axis.size > 1: newaxes.append(axis)
    return signal.nxdata.view().reshape(shape), newaxes


def centers(signal, axes):
    """
    Return the centers of the axes.

    This works regardless if the axes contain bin boundaries or centers.
    """
    def findc(axis, dimlen):
        if axis.shape[0] == dimlen+1:
            return (axis.nxdata[:-1] + axis.nxdata[1:])/2
        else:
            assert axis.shape[0] == dimlen
            return axis.nxdata
    return [findc(a,signal.shape[i]) for i,a in enumerate(axes)]


def label(field):
    """
    Return a label for a data field suitable for use on a graph axis.
    """
    if hasattr(field, 'long_name'):
        return field.long_name
    elif hasattr(field, 'units'):
        return "%s (%s)"%(field.nxname, field.units)
    else:
        return field.nxname


class PylabPlotter(object):

    """
    Matplotlib plotter class for NeXus data.
    """

    def plot(self, data, fmt, xmin, xmax, ymin, ymax, zmin, zmax, **opts):
        """
        Plot the data entry.

        Raises NeXusError if the data cannot be plotted.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise NeXusError("Default plotting package (matplotlib) not available.")

        over = False
        if "over" in opts.keys():
            if opts["over"]: 
                over = True
            del opts["over"]

        log = logx = logy = False
        if "log" in opts.keys():
            if opts["log"]: log = True
            del opts["log"]
        if "logy" in opts.keys():
            if opts["logy"]: logy = True
            del opts["logy"]
        if "logx" in opts.keys():
            if opts["logx"]: logx = True
            del opts["logx"]
        if fmt == '': 
            fmt = 'o'

        if over:
            plt.autoscale(enable=False)
        else:
            plt.autoscale(enable=True)
            plt.clf()

        signal = data.nxsignal
        axes = data.nxaxes
        errors = data.nxerrors
        title = data.nxtitle

        # Provide a new view of the data if there is a dimension of length 1
        if 1 in signal.shape:
            data, axes = _fixaxes(signal, axes)
        else:
            data = signal.nxdata

        # Find the centers of the bins for histogrammed data
        axis_data = centers(data, axes)

        #One-dimensional Plot
        if len(data.shape) == 1:
            if hasattr(signal, 'units'):
                if not errors and signal.units == 'counts':
                    errors = NXfield(np.sqrt(data))
            if errors:
                ebars = errors.nxdata
                plt.errorbar(axis_data[0], data, ebars, fmt=fmt, **opts)
            else:
                plt.plot(axis_data[0], data, fmt, **opts)
            if not over:
                ax = plt.gca()
                xlo, xhi = ax.set_xlim(auto=True)        
                ylo, yhi = ax.set_ylim(auto=True)                
                if xmin: xlo = xmin
                if xmax: xhi = xmax
                ax.set_xlim(xlo, xhi)
                if ymin: ylo = ymin
                if ymax: yhi = ymax
                ax.set_ylim(ylo, yhi)
                if logx: ax.set_xscale('symlog')
                if log or logy: ax.set_yscale('symlog')
                plt.xlabel(label(axes[0]))
                plt.ylabel(label(signal))
                plt.title(title)

        #Two dimensional plot
        else:
            from matplotlib.image import NonUniformImage
            from matplotlib.colors import LogNorm, Normalize

            if len(data.shape) > 2:
                slab = [slice(None), slice(None)]
                for _dim in data.shape[2:]:
                    slab.append(0)
                data = data[slab].view().reshape(data.shape[:2])
                print "Warning: Only the top 2D slice of the data is plotted"

            x = axis_data[1]
            y = axis_data[0]
            if not zmin: 
                zmin = np.nanmin(data)
            if not zmax: 
                zmax = np.nanmax(data)
            
            if log:
                zmin = max(zmin, 0.01)
                zmax = max(zmax, 0.01)
                opts["norm"] = LogNorm(zmin, zmax)
            else:
                opts["norm"] = Normalize(zmin, zmax)

            ax = plt.gca()
            extent = (x[0],x[-1],y[0],y[-1])
            im = NonUniformImage(ax, extent=extent, origin=None, **opts)
            im.set_data(x, y, data)
            im.get_cmap().set_bad('k', 1.0)
            ax.images.append(im)
            xlo, xhi = ax.set_xlim(x[0], x[-1])
            ylo, yhi = ax.set_ylim(y[0], y[-1])
            if xmin: 
                xlo = xmin
            else:
                xlo = x[0]
            if xmax: 
                xhi = xmax
            else:
                xhi = x[-1]
            if ymin: 
                yhi = ymin
            else:
                yhi = y[0]
            if ymax: 
                yhi = ymax
            else:
                yhi = y[-1]
            ax.set_xlim(xlo, xhi)
            ax.set_ylim(ylo, yhi)
            plt.xlabel(label(axes[0]))
            plt.ylabel(label(axes[1]))
            plt.title(title)
            plt.colorbar(im)

        plt.gcf().canvas.draw_idle()
        plt.ion()
        plt.show()


plotview = PylabPlotter()

