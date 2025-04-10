# -----------------------------------------------------------------------------
# Copyright (c) 2013-2025, NeXpy Development Team.
#
# Author: Paul Kienzle, Ray Osborn
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------

"""Module to provide standard Matplotlib plotting to the NeXus Python API."""
import copy

import numpy as np

from . import NeXusError, NXfield


def centers(axis, dimlen):
    """Return the centers of the axis bins.

    This works regardless of whether the axis consists of bin boundaries,
    i.e, `dimlen = len(axis) + 1``, or centers, i.e., `dimlen = len(axis)`.

    Parameters
    ----------
    axis : ndarray
        Array containing the axis values.
    dimlen : int
        Length of corresponding data dimension.

    Returns
    -------
    ndarray
        Array of bin centers with a size of dimlen.
    """
    ax = axis.astype(np.float64)
    if ax.shape[0] == dimlen+1:
        return (ax[:-1] + ax[1:])/2
    else:
        assert ax.shape[0] == dimlen
        return ax


def boundaries(axis, dimlen):
    """Return the axis bin boundaries.

    This works regardless of whether the axis consists of bin boundaries,
    i.e, dimlen = len(axis) + 1, or centers, i.e., dimlen = len(axis).

    Parameters
    ----------
    axis : ndarray
        Array containing the axis values.
    dimlen : int
        Length of corresponding data dimension.

    Returns
    -------
    ndarray
        Array of bin boundaries with a size of dimlen + 1.
    """
    ax = axis.astype(np.float64)
    if ax.shape[0] == dimlen:
        start = ax[0] - (ax[1] - ax[0])/2
        end = ax[-1] + (ax[-1] - ax[-2])/2
        return np.concatenate((np.atleast_1d(start),
                               (ax[:-1] + ax[1:])/2,
                               np.atleast_1d(end)))
    else:
        assert ax.shape[0] == dimlen + 1
        return ax


def label(field):
    """Return a label for a data field suitable for use on a graph axis.

    This returns the attribute 'long_name' if it exists, or the field name,
    followed by the units attribute if it exists.

    Parameters
    ----------
    field : NXfield
        NeXus field used to construct the label.

    Returns
    -------
    str
        Axis label.
    """
    if 'long_name' in field.attrs:
        return field.long_name
    elif 'units' in field.attrs:
        return f"{field.nxname} ({field.units})"
    else:
        return field.nxname


class PyplotPlotter:
    """Matplotlib plotter class for 1D or 2D NeXus data.

    When the nexusformat package is used within NeXpy, plots are produced by
    calling the NXPlotView class function, 'plot'. This provides a function
    with the same call signature for use outside NeXpy.
    """

    def plot(self, data_group, fmt=None, xmin=None, xmax=None,
             ymin=None, ymax=None, vmin=None, vmax=None, **kwargs):
        """Plot the NXdata group.

        Parameters
        ----------
        data_group : NXdata
            NeXus group containing the data to be plotted.
        fmt : str, optional
            Formatting options that are compliant with PyPlot, by default None
        xmin : float, optional
            Minimum x-boundary, by default None
        xmax : float, optional
            Maximum x-boundary, by default None
        ymin : float, optional
            Minimum y-boundary, by default None
        ymax : float, optional
            Maximum y-boundary, by default None
        vmin : float, optional
            Minimum signal value for 2D plots, by default None
        vmax : float, optional
            Maximum signal value for 2D plots, by default None
        **kwargs : dict
            Options used to customize the plot.

        Note
        ----
        If the qualitative color map, 'tab10', is specified as a
        keyword argument, the color scale is chosen so that all the
        integer values are centered on each color band, if the
        maximum intensity is less than 10.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise NeXusError(
                "Default plotting package (matplotlib) not available.")

        over = kwargs.pop("over", False)
        image = kwargs.pop("image", False)
        log = kwargs.pop("log", False)
        logx = kwargs.pop("logx", False)
        logy = kwargs.pop("logy", False)
        origin = kwargs.pop("origin", "lower")
        aspect = kwargs.pop("aspect", "auto")
        regular = kwargs.pop("regular", False)
        cmap = kwargs.pop("cmap", "viridis")
        colorbar = kwargs.pop("colorbar", True)
        interpolation = kwargs.pop("interpolation", "nearest")
        bad = kwargs.pop("bad", "darkgray")
        weights = kwargs.pop("weights", False)
        ax = kwargs.pop("ax", None)

        signal = data_group.nxsignal
        if signal.ndim > 2 and not image:
            raise NeXusError(
                "Can only plot 1D and 2D data - please select a slice")
        errors = data_group.nxerrors
        title = data_group.nxtitle
        coordinates = data_group.nxcoordinates

        # Provide a new view of the data if there is a dimension of length 1
        if len(coordinates) > 0:
            data = signal.nxdata
        else:
            data, axes = (signal.nxdata.reshape(data_group.plot_shape),
                          data_group.plot_axes)

        if weights and data_group.nxweights:
            with np.errstate(divide='ignore'):
                w = data_group.nxweights.nxdata.reshape(data_group.plot_shape)
                data = np.where(w > 0, data/w, 0.0)

        isinteractive = plt.isinteractive()
        plt.ioff()

        try:
            if over:
                plt.autoscale(False)
            else:
                plt.autoscale(True)
                if ax is None:
                    plt.clf()
            if ax:
                plt.sca(ax)
            else:
                ax = plt.gca()

            # One-dimensional Plot
            if len(data.shape) == 1 and len(coordinates) == 0:
                if 'marker' in kwargs:
                    fmt = kwargs.pop('marker')
                else:
                    fmt = 'o'
                if 'units' in signal.attrs:
                    if not errors and signal.attrs['units'] == 'counts':
                        errors = NXfield(np.sqrt(data))
                if errors:
                    ebars = errors.nxdata
                    ax.errorbar(centers(axes[0], data.shape[0]), data, ebars,
                                fmt=fmt, **kwargs)
                else:
                    ax.plot(centers(axes[0], data.shape[0]), data, fmt,
                            **kwargs)
                if not over:
                    if xmin is not None:
                        ax.set_xlim(left=xmin)
                    if xmax is not None:
                        ax.set_xlim(right=xmax)
                    if ymin is not None:
                        ax.set_ylim(bottom=ymin)
                    if ymax is not None:
                        ax.set_ylim(top=ymax)
                    if logx:
                        ax.set_xscale('log')
                    if log or logy:
                        ax.set_yscale('log')
                    plt.xlabel(label(axes[0]))
                    plt.ylabel(label(signal))
                    plt.title(title)

            if len(data.shape) == 1 and len(coordinates) > 0:
                if 'size' in kwargs:
                    s = kwargs.pop('size')
                else:
                    s = 50
                if len(coordinates) == 1:
                    x = coordinates[0].nxdata
                    ax.scatter(x, data, s=s, **kwargs)
                elif len(coordinates) == 2:
                    y = coordinates[0].nxdata
                    x = coordinates[1].nxdata
                    ax.scatter(x, y, c=data, s=s, **kwargs)
                else:
                    raise NeXusError("Cannot plot more than two coordinates.")
                if not over:
                    if xmin is not None:
                        ax.set_xlim(left=xmin)
                    if xmax is not None:
                        ax.set_xlim(right=xmax)
                    if ymin is not None:
                        ax.set_ylim(bottom=ymin)
                    if ymax is not None:
                        ax.set_ylim(top=ymax)
                    if logx:
                        ax.set_xscale('log')
                    if log or logy:
                        ax.set_yscale('log')
                    if len(coordinates) == 1:
                        plt.xlabel(label(coordinates[0]))
                        plt.ylabel(label(signal))
                    else:
                        plt.xlabel(label(coordinates[1]))
                        plt.ylabel(label(coordinates[0]))
                    plt.title(title)

            # Two dimensional plot
            else:
                from matplotlib.colors import LogNorm, Normalize

                if image:
                    x = boundaries(axes[-1], data.shape[-2])
                    y = boundaries(axes[-2], data.shape[-3])
                    xlabel, ylabel = label(axes[-1]), label(axes[-2])
                else:
                    x = boundaries(axes[-1], data.shape[-1])
                    y = boundaries(axes[-2], data.shape[-2])
                    xlabel, ylabel = label(axes[-1]), label(axes[-2])

                if not vmin:
                    vmin = np.nanmin(data[data > -np.inf])
                if not vmax:
                    vmax = np.nanmax(data[data < np.inf])

                if image:
                    im = ax.imshow(data, origin='upper', **kwargs)
                    ax.set_aspect('equal')
                else:
                    from packaging.version import Version
                    from matplotlib import __version__ as mplversion

                    if log:
                        vmin = max(vmin, 0.01)
                        vmax = max(vmax, 0.01)
                        kwargs["norm"] = LogNorm(vmin, vmax)
                    else:
                        kwargs["norm"] = Normalize(vmin, vmax)

                    if Version(mplversion) >= Version('3.5.0'):
                        from matplotlib import colormaps
                        cm = copy.copy(colormaps[cmap])
                    else:
                        from matplotlib.cm import get_cmap
                        cm = copy.copy(get_cmap(cmap))
                    cm.set_bad(bad, 1.0)
                    if regular:
                        extent = (x[0], x[-1], y[0], y[-1])
                        kwargs['interpolation'] = interpolation
                        im = ax.imshow(data, origin=origin, extent=extent,
                                       cmap=cm, **kwargs)
                    else:
                        im = ax.pcolormesh(x, y, data, cmap=cm, **kwargs)
                        ax.set_xlim(x[0], x[-1])
                        ax.set_ylim(y[0], y[-1])
                    if aspect == 'equal':
                        try:
                            if 'scaling_factor' in axes[-1].attrs:
                                _xscale = axes[-1].attrs['scaling_factor']
                            else:
                                _xscale = 1.0
                            if 'scaling_factor' in axes[-2].attrs:
                                _yscale = axes[-2].attrs['scaling_factor']
                            else:
                                _yscale = 1.0
                            aspect = float(_yscale / _xscale)
                        except Exception as error:
                            raise NeXusError(str(error))
                    ax.set_aspect(aspect)
                    if colorbar:
                        cb = plt.colorbar(im)
                        if cmap == 'tab10':
                            cmin, cmax = im.get_clim()
                            if cmax - cmin <= 9:
                                if cmin == 0:
                                    im.set_clim(-0.5, 9.5)
                                elif cmin == 1:
                                    im.set_clim(0.5, 10.5)
                                if Version(mplversion) >= Version('3.5.0'):
                                    cb.ax.set_ylim(cmin-0.5, cmax+0.5)
                                    cb.set_ticks(range(int(cmin), int(cmax)+1))

                if xmin is not None:
                    ax.set_xlim(left=xmin)
                if xmax is not None:
                    ax.set_xlim(right=xmax)
                if ymin is not None:
                    if image:
                        ax.set_ylim(top=ymin)
                    else:
                        ax.set_ylim(bottom=ymin)
                if ymax is not None:
                    if image:
                        ax.set_ylim(bottom=ymax)
                    else:
                        ax.set_ylim(top=ymax)

                plt.xlabel(xlabel)
                plt.ylabel(ylabel)
                plt.title(title)

            if isinteractive:
                plt.pause(0.001)
                plt.show(block=False)
            else:
                plt.show()

        finally:
            if isinteractive:
                plt.ion()


plotview = PyplotPlotter()
