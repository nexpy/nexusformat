# -----------------------------------------------------------------------------
# Copyright (c) 2024-2025, Kaitlyn Marlor, Ray Osborn, Justin Wozniak.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------
import logging
import os
import re
import shutil
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    from importlib_resources import files as package_files
else:
    from importlib.resources import files as package_files

import numpy as np
from colored import Fore, Style
from dateutil.parser import parse


name_pattern = re.compile(r'^[a-zA-Z0-9_]([a-zA-Z0-9_.]*[a-zA-Z0-9_])?$')


def get_logger():
    """
    Returns a logger instance and sets the log level to DEBUG.

    The logger has a stream handler that writes to sys.stdout.

    Returns
    -------
    logger : logging.Logger
        A logger instance.
    """
    logger = logging.getLogger("NXValidate")
    logger.setLevel(logging.WARNING)
    logger.propagate = False
    nexpy_running = False
    try:
        from nexpy.gui.pyqt import QtWidgets
        app = QtWidgets.QApplication.instance()
        if app and app.applicationName() == "nexpy":
            nexpy_running = True
    except Exception:
        pass
    if nexpy_running:
        from nexpy.gui.utils import NXValidationHandler
        gui_handler = NXValidationHandler(capacity=1000)
        gui_handler.setFormatter(NXFormatter('%(message)s'))
        logger.addHandler(gui_handler)
    else:
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setFormatter(NXFormatter('%(message)s'))    
        logger.addHandler(stream_handler)
    logger.total = {'warning': 0, 'error': 0}
    return logger


def get_log_level(level='warning'):
    """
    Converts a given log level to its corresponding logging constant.

    Parameters
    ----------
    level : str or int
        The log level to be converted. Can be 'info', 'debug',
        'warning', or 'error', or the corresponding logging constants.

    Returns
    -------
    log_level : int
        The converted log level.

    """
    if level == 'info' or level == logging.INFO:
        return logging.INFO
    elif level == 'debug' or level == logging.DEBUG:
        return logging.DEBUG
    elif level == 'warning' or level == 'warnings' or level == logging.WARNING:
        return logging.WARNING
    elif level == 'error' or level == 'errors' or level == logging.ERROR:
        return logging.ERROR


def is_valid_name(name):
    """
    Checks if a given name is valid according to the defined name pattern.

    Parameters
    ----------
    name : str
        The name to be validated.

    Returns
    -------
    bool
        True if the name is valid, False otherwise.
    """
    if re.match(name_pattern, name):
        return True
    else:
        return False


def is_valid_iso8601(date_string):
    """
    Checks if a given date is valid according to the ISO 8601 standard.

    Parameters
    ----------
    date_string : str
        The date string to be validated.

    Returns
    -------
    bool
        True if the date string is valid, False otherwise.
    """
    try:
        parse(date_string)
        return True
    except ValueError:
        return False


def is_valid_int(dtype):
    """
    Checks if a given data type is a valid integer type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid integer type, False otherwise.
    """
    return np.issubdtype(dtype, np.integer) 


def is_valid_float(dtype):
    """
    Checks if a given data type is a valid floating point type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid floating point type, False
        otherwise.
    """
    return np.issubdtype(dtype, np.floating)


def is_valid_bool(dtype):
    """
    Checks if a given data type is a valid boolean type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid boolean type, False otherwise.
    """
    return np.issubdtype(dtype, np.bool_) 


def is_valid_char(dtype):
    """
    Checks if a given data type is a valid character type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid character type, False
        otherwise.
    """
    from .tree import string_dtype
    return (np.issubdtype(dtype, np.str_) or  np.issubdtype(dtype, np.bytes_)
            or dtype == string_dtype)


def is_valid_char_or_number(dtype):
    """
    Checks if a given data type is a valid character or number type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid character or number type, False
        otherwise.
    """
    return is_valid_char(dtype) or is_valid_number(dtype)


def is_valid_complex(dtype):
    """
    Checks if a given data type is a valid complex number type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid complex type, False otherwise.
    """
    return np.issubdtype(dtype, np.complex) 


def is_valid_number(dtype):
    """
    Checks if a given data type is a valid number type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid number type, False otherwise.
    """
    return np.issubdtype(dtype, np.number) 


def is_valid_posint(dtype):
    """
    Checks if a given data type is a valid positive integer type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid positive integer type, False
        otherwise.
    """
    if np.issubdtype(dtype, np.integer):
         info = np.iinfo(dtype)
         return info.max > 0
    return False 


def is_valid_uint(dtype):
    """
    Checks if a given data type is a valid unsigned integer type.

    Parameters
    ----------
    dtype : type
        The data type to be validated.

    Returns
    -------
    bool
        True if the data type is a valid unsigned integer type, False
        otherwise.
    """
    return np.issubdtype(dtype, np.unsignedinteger) 


def strip_namespace(element):
    """
    Recursively strips namespace from an XML element and its children.

    Parameters
    ----------
    element : xml.etree.ElementTree.Element
        The XML element to strip namespace from.
    """    
    if '}' in element.tag:
        element.tag = element.tag.split('}', 1)[1]
    for child in element:
        strip_namespace(child)


def convert_xml_dict(xml_dict):
    """
    Convert an XML dictionary to a more readable format.

    Parameters
    ----------
    xml_dict : dict
        The XML dictionary to be converted.

    Returns
    -------
    dict
        The converted XML dictionary.

    Notes
    -----
    If the XML dictionary contains '@type' and '@name', it will be
    converted to a dictionary with '@name' as the key. If the XML
    dictionary contains only '@type', it will be converted to a
    dictionary with '@type' as the key. If the XML dictionary does not
    contain '@type' or '@name', it will be returned as is.
    """
    if '@type' in xml_dict:
        if '@name' in xml_dict:
            key = '@name'
        else:
            key = '@type'
    elif '@name' in xml_dict:
        key = '@name'
    else:
        return xml_dict
    return {xml_dict[key]: {k: v for k, v in xml_dict.items() if k != key}}


def xml_to_dict(element):
    """
    Convert an XML element to a dictionary.

    Parameters
    ----------
    element : xml element
        The XML element to be converted.

    Returns
    -------
    dict
        A dictionary representation of the XML element.
    """
    result = {}

    if element.attrib:
        attrs = element.attrib
        for attr in attrs:
            result[f"@{attr}"] = attrs[attr]

    for child in element:
        if child.tag == 'doc' and child.text:
            result[child.tag] = re.sub(r'[\t\n]+', ' ', child.text.strip())
        elif child.tag == 'enumeration':
            result[child.tag] = [item.attrib['value'] for item in child]
        elif child.tag == 'dimensions':
            result[child.tag] =  {}
            if 'rank' in child.attrib:
                result[child.tag].update({'rank': child.attrib['rank']})
            result[child.tag]['dim'] = {}
            for item in [c for c in child if c.tag == 'dim']:
                if 'index' in item.attrib and 'value' in item.attrib:
                    result[child.tag]['dim'].update(
                        {int(item.attrib['index']): item.attrib['value']})
        else:
            child_dict = convert_xml_dict(xml_to_dict(child))       
            if child.tag in result:
                result[child.tag].update(child_dict)
            else:
                result[child.tag] = child_dict

    return result

def merge_dicts(dict1, dict2):
    """
    Recursively merges two dictionaries into one.

    Parameters
    ----------
    dict1 : dict
        The dictionary to be updated.
    dict2 : dict
        The dictionary to update with.

    Returns
    -------
    dict
        The updated dictionary.
    """
    for key, value in dict2.items():
        if (key in dict1 and isinstance(dict1[key], dict)
                and isinstance(value, dict)):
            merge_dicts(dict1[key], value)
        else:
            dict1[key] = value
    return dict1

def readaxes(axes):
    """Return a list of axis names stored in the 'axes' attribute.

    If the input argument is a string, the names are assumed to be separated
    by a delimiter, which can be white space, a comma, or a colon. If it is
    a list of strings, they are converted to strings.

    Parameters
    ----------
    axes : str or list of str
        Value of 'axes' attribute defining the plotting axes.

    Returns
    -------
    list of str
        Names of the axis fields.
    """
    if isinstance(axes, str):
        return list(re.split(r'[,:; ]',
                    str(axes).strip('[]()').replace('][', ':')))
    else:
        return [str(axis) for axis in axes]


def match_strings(pattern_string, target_string):
    # Create regular expression patterns for both cases
    """
    Check if a target string matches a given pattern string, allowing for
    uppercase letters at the start or end of the pattern string.

    Parameters
    ----------
    pattern_string : str
        The string to be matched against.
    target_string : str
        The string to be matched.

    Returns
    -------
    bool
        True if the target string matches the pattern string, False otherwise.
    """
    start_pattern = r'^([A-Z]+)([a-z_]+)$'
    end_pattern = r'^([a-z_]+)([A-Z]+)$'
    
    start_match = re.match(start_pattern, pattern_string)
    end_match = re.match(end_pattern, pattern_string)
    
    if start_match:
        lowercase_part = start_match.group(2)
        target_pattern = f'^[a-z_]+{re.escape(lowercase_part)}$'
        if re.match(target_pattern, target_string):
            return True
    elif end_match:
        lowercase_part = end_match.group(1)
        target_pattern = f'^{re.escape(lowercase_part)}[a-z_]+$'
        if re.match(target_pattern, target_string):
            return True
    
    return False


def get_base_classes(definitions=None):
    """
    Return a list of all base class names.

    Parameters
    ----------
    definitions : str or Path or None
        The path to the NeXus definitions directory (default is None).

    Returns
    -------
    list of str
        A list of NeXus base class names.
    """
    definitions = get_definitions(definitions=definitions)
    base_class_path = definitions.joinpath('base_classes')
    return sorted(
        [str(c.stem[:-5]) for c in base_class_path.glob('*.nxdl.xml')])


def get_definitions(definitions=None):
    """
    Return the path to the NeXus definitions directory.

    If the input argument is given, it is converted to a Path object. If it
    is a string, it is resolved to a full path. If it is None, the path is
    determined from the 'NX_DEFINITIONS' environment variable or, if that
    variable is not set, from the location of the nexusformat package.

    Parameters
    ----------
    definitions : str or Path or None
        The path to the NeXus definitions directory (default is None).

    Returns
    -------
    Path
        The path to the NeXus definitions directory.
    """
    if definitions is not None:
        if isinstance(definitions, str):
            definitions = Path(definitions).resolve()
        elif isinstance(definitions, Path):
            definitions = definitions.resolve()
    elif 'NX_DEFINITIONS' in os.environ:
        definitions = Path(os.environ['NX_DEFINITIONS']).resolve()
    else:
        definitions = multiplex_path(package_files('nexusformat.definitions'))
    return definitions

def multiplex_path(path):
    """
    Convert a MultiplexedPath object to a Path object.

    Parameters
    ----------
    path : str or MultiplexedPath
        The path to be converted.

    Returns
    -------
    Path
        The converted path.
    """
    return Path(re.sub(r"MultiplexedPath\('(.*)'\)", r"\1", str(path)))


def truncate_path(path, max_width=None):
    """Truncate a file path to fit within max_width characters."""
    if max_width is None:
        max_width = terminal_width() - 20
    path = Path(path)
    full_path = path.resolve()
    site_packages = None
    for parent in full_path.parents:
        if parent.name == "site-packages" or parent.name == "src":
            site_packages = parent
            break
    if site_packages:
        full_path = str(full_path.relative_to(site_packages))
    else:
        full_path = str(full_path)
    if len(full_path) > max_width:
        return "..." + full_path[-max_width:]
    return full_path

def terminal_width():
    """
    Returns the width of the terminal in characters.

    Returns
    -------
    int
        The width of the terminal in characters.
    """

    try:
        terminal_width = shutil.get_terminal_size().columns
    except OSError:
        terminal_width = 80
    return terminal_width


def check_nametype(item_value):
    """
    Return the value of the 'nameType' attribute for a given item.

    Parameters
    ----------
    item_value : dict
        The dictionary representation of the item.

    Returns
    -------
    str
        The value of the 'nameType' attribute.
    """
    if '@nameType' in item_value:
        return item_value['@nameType']
    else:
        return 'specified'


def check_dimension_sizes(dimensions):
    """
    Check if a list of values are all within one of each other.
    
    This handles the case where axis bin boundaries are stored.

    Parameters
    ----------
    dimensions : list
        The list of dimensions to be checked.

    Returns
    -------
    bool
        True if dimensions are the same to within ± 1, False otherwise.
    """
    if not dimensions:
        return False
    min_dimension = min(dimensions)
    max_dimension = max(dimensions)
    return max_dimension - min_dimension <= 1


class NXFormatter(logging.Formatter):

    COLORS = {
        'DEBUG': Fore.blue,
        'INFO': Style.reset,
        'WARNING': Fore.rgb(255, 165, 0) + Style.BOLD,
        'ERROR': Fore.red + Style.BOLD,
        'CRITICAL': Style.reset
    }
    
    def format(self, record):
        """Format the specified record as text."""
        log_color = self.COLORS.get(record.levelname, Style.reset)
        message = super().format(record)
        return f"{log_color}{message}{Style.reset}"
