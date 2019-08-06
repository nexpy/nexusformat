#!/usr/bin/env python 
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
# Copyright (c) 2019, NeXpy Development Team.
#
# Author: Paul Kienzle, Ray Osborn
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
#-----------------------------------------------------------------------------

"""
This module provides an extension to allow autocompletion of NeXus object names.

It is derived from h5py.ipy_completer written by Darren Dale.
"""
from __future__ import absolute_import

import posixpath
import re
import readline

from IPython import get_ipython
from IPython.utils import generics
from IPython.core.error import TryNext

from .tree import NXobject

re_attr_match = re.compile(r"(?:.*\=)?(?:.*\()?(?:.*,)?(.+\[.*\].*)\.(\w*)$")
re_item_match = re.compile(r"""(?:.*\=)?(?:.*\()?(?:.*,)?(.*)\[(?P<s>['|"])(?!.*(?P=s))(.*)$""")
re_object_match = re.compile(r"(?:.*\=)?(?:.*\()?(?:.*,)?(.+?)(?:\[)")


def _retrieve_obj(name, context):
    """ Filter function for completion. """

    # we don't want to call any functions, but I couldn't find a robust regex
    # that filtered them without unintended side effects. So keys containing
    # "(" will not complete.
    
    if '(' in name:
        raise ValueError()

    return eval(name, context.user_ns)


def nxitem_completer(context, command):
    """Compute possible item matches for dict-like objects"""

    base, item = re_item_match.split(command)[1:4:2]

    try:
        obj = _retrieve_obj(base, context)
    except Exception:
        return []

    path, _ = posixpath.split(item)
    if path:
        items = (posixpath.join(path, name) for name in obj[path].iterkeys())
    else:
        items = obj.iterkeys()
    items = list(items)

    readline.set_completer_delims(' \t\n`!@#$^&*()=+[{]}\\|;:\'",<>?')
    item_list = [i for i in items if i[:len(item)] == item]
    return [i for i in items if i[:len(item)] == item]


def nxattr_completer(context, command):
    """Compute possible attr matches for nested dict-like objects"""

    base, attr = re_attr_match.split(command)[1:3]
    base = base.strip()

    try:
        obj = _retrieve_obj(base, context)
    except Exception:
        return []

    attrs = dir(obj)
    try:
        attrs = generics.complete_object(obj, attrs)
    except TryNext:
        pass

    omit__names = get_ipython().Completer.omit__names
    if omit__names == 1:
        attrs = [a for a in attrs if not a.startswith('__')]
    elif omit__names == 2:
        attrs = [a for a in attrs if not a.startswith('_')]

    readline.set_completer_delims(' =')

    return [".%s" % a for a in attrs if a[:len(attr)] == attr]


def nxcompleter(self, event):
    """ Completer function to be loaded into IPython """
    base = re_object_match.split(event.line)[1]

    if not isinstance(self._ofind(base)['obj'], NXobject):
        raise TryNext

    try:
        return nxattr_completer(self, event.line)
    except ValueError:
        pass

    try:
        return nxitem_completer(self, event.line)
    except ValueError:
        pass

    return []


def load_ipython_extension(ip=None):
    """ Load completer function into IPython """
    if ip is None:
        ip = get_ipython()
    ip.Completer.use_jedi = False
    ip.set_hook('complete_command', nxcompleter, re_key=r"(?:.*\=)?(.+?)\[")
