# -----------------------------------------------------------------------------
# Copyright (c) 2019-2021, NeXpy Development Team.
#
# Author: Paul Kienzle, Ray Osborn
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------

"""IPython extension to allow autocompletion of NeXus object names.

This modifies h5py.ipy_completer, written by Darren Dale, to accommodate
the completion of NeXus paths defined as nested dictionaries. It will also
autocomplete attributes at the end of a dictionary path. The NeXus objects
can follow an assignment or be embedded in function arguments.

Examples
--------
Autocompletion works on each component of the following commands::

>>> signal = root[entry/data/signal]
>>> units = root[entry/data/signal].units
>>> data = NXdata(root[entry/data/signal])

"""
import re

try:
    import readline
except ImportError:
    readline = None
from string import punctuation

from .tree import NeXusError, NXobject

re_attr_match = re.compile(r"(.+\[.*\].*)\.(\w*)$")
re_item_match = re.compile(r"""(.*)\[(?P<s>['|"])(?!.*(?P=s))(.*)$""")
re_object_match = re.compile(r"(.+?)(?:\[)")


def _retrieve_obj(name, shell):
    """Retrieve the NeXus object at the base of the command.

    This filters out invalid characters not caught by the regex.

    Parameters
    ----------
    name : str
        Name of the object to be retrieved.
    shell : InteractiveShell
        IPython shell containing the namespace to be searched.

    Returns
    -------
    NXobject
        The NeXus object at the base of the command.

    Raises
    ------
    ValueError
        If the object name contains a '('.
    """

    if '(' in name:
        raise ValueError()

    return eval(name, shell.user_ns)


def nxitem_completer(shell, command):
    """Compute possible dictionary matches for NXgroups or NXfields.

    This matches NeXus objects referenced as nested dictionary paths.

    Parameters
    ----------
    shell : InteractiveShell
        IPython shell containing the namespace to be searched.
    command : str
        Command to be autocompleted

    Returns
    -------
    list of str
        List of possible completions.
    """
    base, item = re_item_match.split(command)[1:4:2]

    try:
        obj = _retrieve_obj(base, shell)
    except Exception:
        return []

    import posixpath
    path, _ = posixpath.split(item)
    try:
        if path:
            items = (posixpath.join(path, name) for name in obj[path].keys())
        else:
            items = obj.keys()
    except Exception:
        items = []
    items = list(items)

    readline.set_completer_delims(' \t\n`!@#$^&*()=+[{]}\\|;:\'",<>?')
    return [i for i in items if i[:len(item)] == item]


def nxattr_completer(shell, command):
    """Compute possible matches for NXgroup or NXfield attributes.

    This matches attributes at the end of NeXus dictionary references.
    If the entire NeXus path is defined using attribute references, then
    the autocompletion is handled by other completers.

    Parameters
    ----------
    shell : InteractiveShell
        IPython shell containing the namespace to be searched.
    command : str
        Command to be autocompleted

    Returns
    -------
    list of str
        List of possible completions.
    """
    from IPython import get_ipython
    from IPython.core.error import TryNext
    from IPython.utils import generics
    base, attr = re_attr_match.split(command)[1:3]
    base = base.strip()

    try:
        obj = _retrieve_obj(base, shell)
    except Exception:
        return []

    attrs = obj._get_completion_list()
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

    return [f".{a}" for a in attrs if a[:len(attr)] == attr]


def nxcompleter(shell, event):
    """Completer function to be loaded into IPython.

    Only text that ends with a valid NXobject is inspected.

    Parameters
    ----------
    shell : InteractiveShell
        IPython shell containing the namespace to be searched.
    event :
        IPython object containing the command to be completed.

    Returns
    -------
    list of str
        List of possible completions.

    Raises
    ------
    TryNext
        If no completions are found.
    """
    from IPython.core.error import TryNext

    if readline is None:
        raise NeXusError(
            "Install the readline module to enable tab completion")

    command = re.split('[ !#$%&()*+,:;<=>?@^~]',
                       event.line)[-1].lstrip(punctuation)
    try:
        base = re_object_match.split(command)[1]
    except Exception:
        raise TryNext

    try:
        obj = shell._ofind(base).obj
    except AttributeError:
        obj = shell._ofind(base).get('obj')
    if not isinstance(obj, NXobject):
        raise TryNext

    try:
        return nxattr_completer(shell, command)
    except ValueError:
        pass

    try:
        return nxitem_completer(shell, command)
    except ValueError:
        pass

    return []


def load_ipython_extension(ip=None):
    """Load completer function into IPython.

    This calls the IPython set_hook function to add nxcompleter to the list of
    completer functions. This function disables the use of Jedi autcompletion,
    which is currently incompatible with the nexusformat classes.

    Parameters
    ----------
    ip : InteractiveShell, optional
        IPython shell to be modified. By default, it is set by get_ipython().
    """
    from IPython import get_ipython
    if readline is None:
        raise NeXusError(
            "Install the readline module to enable tab completion")
    if ip is None:
        ip = get_ipython()
    ip.Completer.use_jedi = False
    ip.set_hook('complete_command', nxcompleter,
                re_key=r"(?:.*\=)?(?:.*\()?(?:.*,)?(.+?)\[")
