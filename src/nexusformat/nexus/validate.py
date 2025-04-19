# -----------------------------------------------------------------------------
# Copyright (c) 2024-2025, Kaitlyn Marlor, Ray Osborn, Justin Wozniak.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING, distributed with this software.
# -----------------------------------------------------------------------------
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from . import NeXusError, NXentry, NXfield, NXgroup, NXlink, NXsubentry, nxopen
from .utils import (check_dimension_sizes, check_nametype, get_definitions,
                    get_log_level, get_logger, is_valid_bool, is_valid_char,
                    is_valid_char_or_number, is_valid_complex, is_valid_float,
                    is_valid_int, is_valid_iso8601, is_valid_name,
                    is_valid_number, is_valid_posint, is_valid_uint,
                    match_strings, merge_dicts, readaxes, strip_namespace,
                    truncate_path, xml_to_dict)

logger = get_logger()


validators = {}


def get_validator(nxclass, definitions=None):
    """
    Retrieves a validator instance for a given NeXus class.

    Validators are stored in a global dictionary. If a validator has not
    already been created yet, it is created.

    Parameters
    ----------
    nxclass : str
        The name of the NeXus class to retrieve a validator for.

    Returns
    -------
    Validator
        A validator instance for the specified NeXus class.
    """
    if nxclass not in validators:
        validator = GroupValidator(nxclass, definitions=definitions)
        nxclass = validator.nxclass
        validators[nxclass] = validator
    elif (definitions is not None and
          Path(definitions).resolve() != validators[nxclass].definitions):
        validators[nxclass] = GroupValidator(nxclass, definitions=definitions)
    return validators[nxclass]


class Validator():
    
    def __init__(self, definitions=None):
        """
        Initializes a new Validator instance.
        """
        self.definitions = get_definitions(definitions=definitions)
        self.baseclasses = self.definitions / 'base_classes'
        if not self.baseclasses.exists():
            raise NeXusError(f'"{self.baseclasses}" does not exist')
        self.applications = self.definitions / 'applications'
        if not self.applications.exists():
            self.applications = None
        self.contributions = self.definitions / 'contributed_definitions'
        if not self.contributions.exists():
            self.contributions = None
        self.filepath = None
        self.parent = None
        self.logged_messages = []
        self.indent = 0

    def __repr__(self):
        return f'{self.__class__.__name__}({self.filepath.stem})'

    def get_attributes(self, element):
        """
        Retrieves the attributes of a given XML item as a dictionary.

        Parameters
        ----------
        element : XML.Element
            The item from which to retrieve attributes.

        Returns
        -------
        dict
            A dictionary containing the item's attributes.
        """
        try:
            result = {}
            result = {f"@{k}": v for k, v in element.attrib.items()}
            for child in element:
                if child.tag == 'enumeration':
                    result[child.tag] = [item.attrib['value']
                                         for item in child]
                elif child.tag != 'doc':
                    result[child.tag] = self.get_attributes(child)
            return result
        except Exception:
            return {}

    def is_valid_link(self, item):
        """
        Checks if the target to an external link exists.

        Parameters
        ----------
        item : NXlink or NXfield
            The item to check.

        Returns
        -------
        bool
            True if the target exists, False otherwise.
        """
        if item.is_external():
            target = f'{item._filename}[{item._target}]'
        else:
            target = item._target
        if item.exists():
            if isinstance(item, NXfield):
                self.log(f'This field is linked to "{target}"', level='info')
            elif isinstance(item, NXgroup):
                self.log(f'This group is linked to "{target}"', level='info')
            return True
        else:
            self.log(f'This is a broken link to "{target}"', level='error')
            return False

    def log(self, message, level='info', indent=None):
        """
        Logs a message with a specified level and indentation.

        Parameters
        ----------
        message : str
            The message to be logged.
        level : str, optional
            The level of the message (default is 'info').
        indent : int, optional
            The indentation level of the message (default is None).
        """
        if indent is None:
            indent = self.indent
        self.logged_messages.append((message, level, indent))

    def output_log(self):
        """
        Outputs the logged messages and resets the log.

        This function iterates over the logged messages, counts the
        number of messages at each level, and logs each message using
        the log function. If the logger level is set to WARNING or ERROR
        and there are no messages at that level, the function resets the
        log and returns without logging any messages.
        """
        warning = 0
        error = 0
        for item in self.logged_messages:
            if item[1] == 'warning':
                warning += 1
            elif item[1] == 'error':
                error += 1
        if ((logger.level == logging.WARNING and warning == 0 and error == 0)
                or (logger.level == logging.ERROR and error == 0)):
            self.logged_messages = []
            return
        if self.parent is None:
            for message, level, indent in self.logged_messages:
                log(message, level=level, indent=indent)
        else:
            self.parent.logged_messages.extend(self.logged_messages)
        self.logged_messages = []


class GroupValidator(Validator):

    def __init__(self, nxclass, definitions=None):
        """
        Initializes the GroupValidator instance.

        Parameters
        ----------
        nxclass : str
            The name of the NeXus class for which to create a validator.
        definitions : str, optional
            The path to the directory containing the NeXus base class
            definitions (default is None).
        """
        super().__init__(definitions=definitions)
        self.nxclass = nxclass
        if self.nxclass is None or self.nxclass == 'NXgroup':
            self.xml_dict = None
            self.valid_class = False
        else:
            self.xml_dict = self.get_xml_dict()
        self.get_valid_fields()
        self.get_valid_groups()
        self.get_valid_attributes()

    def get_xml_dict(self):
        """
        Retrieves the root element of the NeXus class XML file.

        If the NeXus class is specified and the corresponding XML file
        exists, this method parses the file and returns its root
        element. Otherwise, it returns None.

        Returns
        -------
        root : ElementTree.Element or None
            The root element of the NeXus class definition XML file, or
            None if the class is not specified or the file does not
            exist.
        """
        class_path = None
        if self.nxclass:
            if Path(self.nxclass).exists():
                class_path = Path(self.nxclass)
                self.nxclass = Path(self.nxclass).stem.replace('.nxdl', '')
            else:
                class_path = self.baseclasses / (f'{self.nxclass}.nxdl.xml')
                if not class_path.exists():
                    if self.contributions is not None:
                        class_path = (
                            self.contributions / (f'{self.nxclass}.nxdl.xml'))

        if class_path is not None and class_path.exists():
            self.filepath = class_path.resolve()
            tree = ET.parse(class_path)
            root = tree.getroot()
            strip_namespace(root)
            xml_dict = xml_to_dict(root)
            self.valid_class = True
            if '@ignoreExtraAttributes' in xml_dict:
                self.ignoreExtraAttributes = True
            else:
                self.ignoreExtraAttributes = False
            if '@ignoreExtraFields' in xml_dict:
                self.ignoreExtraFields = True
            else:
                self.ignoreExtraFields = False
            if '@ignoreExtraGroups' in xml_dict:
                self.ignoreExtraGroups = True
            else:
                self.ignoreExtraGroups = False
            if '@extends' in xml_dict:
                parent_validator = get_validator(
                    xml_dict['@extends'], definitions=self.definitions)
                xml_extended_dict = parent_validator.get_xml_dict()
                xml_dict = merge_dicts(xml_dict, xml_extended_dict)
            if 'symbols' in xml_dict:
                self.symbols = xml_dict['symbols']['symbol']
            else:
                self.symbols = {}
        else:
            xml_dict = None
            self.valid_class = False
        return xml_dict

    def get_valid_fields(self):
        """
        Retrieves valid fields from the NXDL file.

        This instantiates two dictionaries. The valid_fields dictionary
        contains fields that are defined in the NXDL file with fixed
        names. The partial_fields dictionary contains fields whose names
        have uppercase characters that can be substituted for the actual
        name in a NeXus file.
        """
        valid_fields = {}
        partial_fields = {}
        if self.xml_dict is not None:
            if 'field' not in self.xml_dict:
                self.valid_fields = valid_fields
                self.partial_fields = partial_fields
                return
            fields = self.xml_dict['field']
            for field in fields:
                nameType = check_nametype(fields[field])
                if nameType  == 'any':
                    valid_fields[field] = fields[field]
                    self.ignoreExtraFields = True
                elif nameType == 'partial':
                    partial_fields[field] = fields[field]
                    partial_fields[field]['@name'] = field
                elif nameType == 'specified':
                    valid_fields[field] = fields[field]
                else:
                    self.log(f'The NXDL file uses an invalid name type '
                             f'"{nameType}"', level='error')
        self.valid_fields = valid_fields
        self.partial_fields = partial_fields    

    def get_valid_groups(self):
        """
        Retrieves valid groups from the NXDL file.

        This instantiates two dictionaries. The valid_groups dictionary
        contains groups that are defined in the NXDL file with fixed
        names. The partial_groups dictionary contains groups whose names
        have uppercase characters that can be substituted for the actual
        name in a NeXus file
        """
        valid_groups = {}
        partial_groups = {}
        if self.xml_dict is not None:
            if 'group' not in self.xml_dict:
                self.valid_groups = valid_groups
                self.partial_groups = partial_groups
                return
            groups = self.xml_dict['group']
            for group in groups:
                nameType = check_nametype(groups[group])
                if nameType =='any':
                    valid_groups[group] = groups[group]
                    self.ignoreExtraGroups = True
                elif nameType == 'partial':
                    partial_groups[group] = groups[group]
                    partial_groups[group]['@name'] = group
                elif nameType == 'specified':
                    valid_groups[group] = groups[group]
                else:
                    self.log(f'The NXDL file uses an invalid name type '
                             f'"{nameType}"', level='error')
        self.valid_groups = valid_groups
        self.partial_groups = partial_groups
    
    def get_valid_attributes(self):
        """
        Retrieves valid group attributes from the NXDL file.

        This instantiates two dictionaries. The valid_attributes
        dictionary contains attributes that are defined in the NXDL file
        with fixed names. The partial_attributes dictionary contains
        attributes whose names have uppercase characters that can be
        substituted for the actual name in a NeXus file
        """
        valid_attributes = {}
        partial_attributes = {}
        if self.xml_dict is not None:
            if 'attribute' not in self.xml_dict:
                self.valid_attributes = valid_attributes
                self.partial_attributes = partial_attributes
                return
            attributes = self.xml_dict['attribute']
            for attribute in attributes:
                nameType = check_nametype(attributes[attribute])
                if nameType == 'any':
                    valid_attributes[attribute] = attributes[attribute]
                    self.ignoreExtraAttributes = True
                elif nameType == 'partial':
                    partial_attributes[attribute] = attributes[attribute]
                    partial_attributes[attribute]['@name'] = attribute
                elif nameType == 'specified':
                    valid_attributes[attribute] = attributes[attribute]
                else:
                    self.log(f'The NXDL file uses an invalid name type '
                             f'"{nameType}"', level='error')
        self.valid_attributes = valid_attributes
        self.partial_attributes = partial_attributes

    def check_data(self, group):
        """
        Checks that the signal and axes are present in the group.

        This method also checks that the axes have the correct length
        and that the axis sizes match the signal shape.

        Parameters
        ----------
        group : NXgroup
            The group to be checked.
        """
        if 'signal' in group.attrs:
            signal = group.attrs['signal']
            if signal in group.entries:
                self.log(f'Signal "{signal}" is present in the group',
                         level='info')
                signal_field = group[signal]
            else:
                self.log(f'Signal "{signal}" is not present in the group',
                         level='warning')
                signal = None
        else:
            self.log('"@signal" is not present in the group', level='error')
            signal = None
        if 'axes' in group.attrs:
            axes = readaxes(group.attrs['axes'])
            if signal in group and group[signal].exists():
                if len(axes) != group[signal].ndim:
                    self.log('"@axes" length does not match the signal rank',
                             level='error')
                else:
                    self.log('"@axes" has the correct length')
            for i, axis in enumerate(axes):
                if axis in group.entries:
                    self.log(f'Axis "{axis}" is present in the group',
                             level='info')
                    axis_field = group[axis]
                    if signal in group and group[signal].exists():
                        if check_dimension_sizes(
                            [signal_field.shape[i], axis_field.shape[0]]):
                            self.log(f'Axis "{axis}" size is consistent '
                                     'with the signal shape', level='info')
                        else:
                            self.log(f'Axis "{axis}" size is inconsistent '
                                     'with the signal shape', level='error')
                elif axis != '.':
                    self.log(f'Axis "{axis}" is not present in the group',
                             level='error')
        else:
            self.log('"@axes" is not present in the group', level='warning')

    def reset_symbols(self):
        """
        Resets all symbols dictionaries to be empty.

        This is used to initialize the dictionaries before validating
        a NeXus group.
        """
        for symbol in self.symbols:
            self.symbols[symbol] = {}

    def check_symbols(self, indent=None):
        """
        Checks the values of all symbols in the symbols dictionary.

        This checks for consistency of values of all symbols in the
        symbols dictionary. If the values are all the same, a message is
        logged at the "info" level. If the values are not all the same,
        but all differ by at most 1, a message is logged at the "info"
        level. Otherwise, a message is logged at the "warning" level.

        Parameters
        ----------
        indent : int, optional
            The indentation level for logging (default is 0).
        """
        if indent is not None:
            self.indent = indent
        for symbol in self.symbols:
            values = []
            for entry in [e for e in self.symbols[symbol] if e != 'doc']:
                values.append(self.symbols[symbol][entry])
            if not values:
                continue
            if len(set(values)) == 1:
                self.log(f'All values for "{symbol}" are the same')
                self.indent += 1
                for entry in self.symbols[symbol]:
                    self.log(f'{entry}: {self.symbols[symbol][entry]}')
                self.indent -= 1
            elif check_dimension_sizes(values):
                self.log(f'All values for "{symbol}" are the same (to ±1)')
                self.indent += 1
                for entry in self.symbols[symbol]:
                    self.log(f'{entry}: {self.symbols[symbol][entry]}')
                self.indent -= 1
            else:
                self.log(f'Values for "{symbol}" are not unique',
                         level='warning')
                self.indent += 1
                for entry in self.symbols[symbol]:
                    self.log(f'{entry}: {self.symbols[symbol][entry]}',
                             level='warning')
                self.indent -= 1
            
    def validate(self, group, parent=None, indent=0, level=None): 
        """
        Validates a given group against the NeXus standard.

        This function checks the validity of a group's name, class, and
        attributes. It also recursively validates the group's entries.

        Parameters
        ----------
        group : object
            The group to be validated.
        indent : int, optional
            The indentation level for logging (default is 0).
        level : str, optional
            The logging level (default is None).
        """
        self.parent = parent
        self.indent = indent
        if level is not None:
            logger.setLevel(get_log_level(level))
        self.log(f'{group.nxclass}: {group.nxpath}', level='all')
        self.indent += 1

        if group.nxclass == 'NXgroup':
            if parent.nxclass == 'NXroot':
                self.log('This group has no NeXus base class assigned '
                         'and will not be inspected')
            else:
                self.log('This group has no NeXus base class assigned',
                         level='error')
            self.output_log()
            return

        if not is_valid_name(group.nxname):
            self.log(f'"{group.nxname}" is an invalid name', level='error')
        if isinstance(group, NXlink):
            if not self.is_valid_link(group):
                self.output_log()
                return
        if not self.valid_class:
            self.log(f'{group.nxclass} is not a valid base class',
                     level='error')
            self.output_log()
            return

        parent_group = group.nxgroup
        if group.nxclass != 'NXroot' and group.nxgroup is not None:
            parent_group = group.nxgroup
            parent_validator = get_validator(parent_group.nxclass,
                                             definitions=self.definitions)
            parsed = False
            if group.nxname in parent_validator.valid_groups:
                cls = parent_validator.valid_groups[group.nxname]['@type']
                if group.nxclass != cls:
                    self.log(f'{group.nxname} should have a class of '
                             f'{cls}, not {group.nxclass}', level='error')
                parsed = True
            elif parent_validator.partial_groups:
                for partial_name in parent_validator.partial_groups:
                    if match_strings(partial_name, group.nxname):
                        self.log(f'This group name matches "{partial_name}", '
                         f'which is allowed in {parent_group.nxclass}')
                        parsed = True
            if not parsed:
                if group.nxclass in parent_validator.valid_groups:
                    self.log('This group is a valid class in '
                             f'{parent_group.nxclass}')
                elif group.nxclass not in parent_validator.valid_groups:
                    if parent_validator.ignoreExtraGroups:
                        self.log(f'{group.nxclass} is not defined in '
                                 f'{parent_group.nxclass}. '
                                 'Additional classes are allowed.')
                    else:
                        self.log(f'{group.nxclass} is an invalid class in '
                                 f'{parent_group.nxclass}', level='error')

        for attribute in group.attrs:
            if attribute == 'target':
                continue
            parsed = False
            if attribute in self.valid_attributes:
                self.log(
                    f'"@{attribute}" is a valid attribute in {group.nxclass}')
                parsed = True
            elif self.partial_attributes:
                for partial_name in self.partial_attributes:
                    if match_strings(partial_name, attribute):
                        self.log(
                            f'"@{attribute}" matches "{partial_name}", '
                            f'which is allowed in {group.nxclass}')
                        parsed = True
            if not parsed:
                if self.ignoreExtraAttributes:
                    self.log(
                        f'"@{attribute}" is not defined as an attribute in '
                        f'{group.nxclass}. Additional attributes are allowed.')
                else:
                    self.log(
                        f'"@{attribute}" is not defined as an attribute'
                        f' in {group.nxclass}', level='warning')
        if group.nxclass == 'NXdata':
            self.check_data(group)

        self.reset_symbols()
        for entry in group.entries: 
            item = group.entries[entry]
            if isinstance(item, NXfield):
                if entry in self.valid_fields:
                    tag = self.valid_fields[entry]
                else:
                    tag = None
                    for partial_name in self.partial_fields:
                        if match_strings(partial_name, entry):
                            tag = self.partial_fields[partial_name]
                            break
                field_validator.validate(tag, item, parent=self,
                                         indent=self.indent)
            elif isinstance(item, NXgroup):
                validator = get_validator(item.nxclass,
                                          definitions=self.definitions)
                validator.validate(item, parent=self, indent=self.indent)
        self.check_symbols()
        self.output_log()
        self.indent -= 1
                

class FieldValidator(Validator):

    def __init__(self):
        """
        Initializes a FieldValidator instance.
        """
        super().__init__()

    def check_type(self, field, dtype):
        """
        Checks the data type of a given field.

        Parameters
        ----------
        field : object
            The field to be validated.
        dtype : str
            The NeXus data type to validate against.
        """
        if dtype == 'NX_DATE_TIME': 
            if is_valid_iso8601(field.nxvalue):
                self.log('The field value is a valid NX_DATE_TIME')
            else:
                self.log('The field value is not a valid NX_DATE_TIME',
                         level='warning')
        elif dtype == 'NX_INT':
            if is_valid_int(field.dtype):
                self.log('The field value is a valid NX_INT')
            else:
                self.log('This field is not a valid NX_INT', level='warning')
        elif dtype == 'NX_FLOAT':
            if is_valid_float(field.dtype):
                self.log('The field value is a valid NX_FLOAT')
            else:
                self.log('The field value is not a valid NX_FLOAT',
                         level='warning')
        elif dtype == 'NX_BOOLEAN':
            if is_valid_bool(field.dtype):
                self.log('The field value is a valid NX_BOOLEAN')
            else:
                self.log('The field value is not a valid NX_BOOLEAN',
                         level='warning')         
        elif dtype == 'NX_CHAR':
            if is_valid_char(field.dtype):
                self.log('The field value is a valid NX_CHAR')
            else:
                self.log('The field value is not a valid NX_CHAR',
                         level='warning')                  
        elif dtype == 'NX_CHAR_OR_NUMBER':
            if is_valid_char_or_number(field.dtype):
                self.log('TThe field value is a valid NX_CHAR_OR_NUMBER')
            else:
                self.log('The field value is not a valid NX_CHAR_OR_NUMBER',
                         level='warning')                
        elif dtype == 'NX_COMPLEX':
            if is_valid_complex(field.dtype):
                self.log('The field value is a valid NX_COMPLEX value')
            else:
                self.log('The field value is not a valid NX_COMPLEX value',
                         level='warning') 
        elif dtype == 'NX_NUMBER':
            if is_valid_number(field.dtype):
                self.log('The field value is a valid NX_NUMBER')
            else:
                self.log('The field value is not a valid NX_NUMBER',
                         level='warning')       
        elif dtype == 'NX_POSINT':
            if is_valid_posint(field.dtype):
                self.log('The field value is a valid NX_POSINT')
            else:
                self.log('The field value is not a valid NX_POSINT',
                         level='warning')    
        elif dtype == 'NX_UINT':
            if is_valid_uint(field.dtype):
                self.log('The field value is a valid NX_UINT')
            else:
                self.log('The field value is not a valid NX_UINT',
                         level='warning')        

    def check_dimensions(self, field, dimensions):
        """
        Checks the field dimensions against the specified dimensions.
        
        Parameters
        ----------
        field : 
            The field to check dimensions for.
        dimensions : 
            The base class attribute containing the dimensions to check
            against.
        """
        if 'rank' in dimensions:
            rank = dimensions['rank']
            if rank in self.parent.symbols:
                self.parent.symbols[rank].update({field.nxname: field.ndim})
            else:
                try:
                    rank = int(dimensions['rank'])
                except ValueError:
                    return
                if field.ndim == rank:
                    self.log(f'The field has the correct rank of {rank}')
                else:
                    self.log(f'The field has rank {field.ndim}, '
                             f'should be {rank}', level='warning')
        if 'dim' in dimensions:
            for i, s in dimensions['dim'].items():
                if s in self.parent.symbols:
                    if len(field.shape) > i-1:
                        self.parent.symbols[s].update(
                            {field.nxname: field.shape[i-1]})
                    else:
                        self.log(
                            f'The field rank is {len(field.shape)}, '
                            f'but the dimension index of "{s}" = {i}',
                            level='warning')
                else:
                    try:
                        s = int(s)
                    except ValueError:
                        pass
                    if len(field.shape) > i and field.shape[i-1] == s:
                        self.log(f'The field has the correct size of {s}')
                    else:
                        self.log(f'The field has size {field.shape}, '
                                 f'should be {s}', level='warning')
    
    def check_enumeration(self, field, enumerations):
        """
        Checks if a field's value is a valid member of an enumerated list.

        Parameters
        ----------
        field : 
            The field to check the value for.
        enumerations : 
            The list of valid enumerated values.
        """
        if field.nxvalue in enumerations:
            self.log(
                'The field value is a member of the enumerated list')
        else:
            self.log(
                'The field value is not a member of the enumerated list',
                level='error') 

    def check_attributes(self, field, attributes=None, units=None):
        """
        Checks the attributes of a given field.

        Parameters
        ----------
        field : 
            The field to check attributes for.
        units : optional
            The units of the field. If provided, checks if the units are
            specified in the field attributes.
        """
        if 'signal' in field.attrs:
            self.log(
                'Using "signal" as a field attribute is no longer valid. '
                'Use the group attribute "signal"', level='error')
        elif 'axis' in field.attrs:
            self.log('Using "axis" as a field attribute is no longer valid. '
                     'Use the group attribute "axes"', level='error')
        if 'units' in field.attrs:
            if units:
                self.log(
                    f'"{field.attrs["units"]}" are specified '
                    f'as units of {units}')
            else:
                self.log(f'"{field.attrs["units"]}" are specified as units')
        elif units:
            self.log(f'Units of {units} not specified', level='warning')
        checked_attributes = ['axis', 'signal', 'units']
        if attributes:
            for attr in attributes:
                if attr in field.attrs:
                    self.log(f'The defined attribute "@{attr}" is present')
                    checked_attributes.append(attr)
                elif ('@nameType' in attributes[attr] and
                      attributes[attr]['@nameType'] == 'partial'):
                    for field_attribute in field.attrs:
                        if match_strings(attr, field_attribute):
                            self.log(
                                f'"@{field_attribute}" matches the defined '
                                f'attribute "{attr}"')
                            checked_attributes.append(attr)
                            checked_attributes.append(field_attribute)  
                if attr not in checked_attributes:
                    self.log(
                        f'The defined attribute "@{attr}" is not present')
        for attr in [a for a in field.attrs if a not in checked_attributes]:
            self.log(f'The attribute "@{attr}" is present')

    def validate(self, tag, field, parent=None, minOccurs=None, link=False,
                 indent=0):
        """
        Validates a field in a NeXus group.

        Parameters
        ----------
        tag : dict
            A dictionary containing information about the field.
        field : object
            The field to be validated.
        parent : object, optional
            The parent object. Defaults to None.
        minOccurs : int, optional
            The minimum number of occurrences. Defaults to None.
        link : bool, optional
            True if the field is required to be a link. Defaults to
            False.
        indent : int, optional
            The indentation level. Defaults to 0.
        """
        self.parent = parent
        self.indent = indent
        group = field.nxgroup
        if isinstance(field, NXlink):
            self.log(f'Link: {field.nxpath}', level='all')
        else:
            self.log(f'Field: {field.nxpath}', level='all')
        self.indent += 1
        if not is_valid_name(field.nxname):
            self.log(f'"{field.nxname}" is an invalid name', level='error')
        if link and not isinstance(field, NXlink):
            self.log('This field is not a link as required', level='error')
        if isinstance(field, NXlink):
            if not self.is_valid_link(field):
                self.output_log()
                return
        if minOccurs is not None:
            if minOccurs > 0:
                self.log('This is a required field in the NeXus file')
            else:
                self.log('This is an optional field in the NeXus file')
        elif tag is not None:
            if '@name' in tag:
                self.log(f'This field name matches "{tag["@name"]}", '
                         f'which is allowed in {group.nxclass}')
            else:
                self.log(f'This is a valid field in {group.nxclass}')
        if tag is None:
            if self.parent.ignoreExtraFields is True:
                self.log(f'This field is not defined in {group.nxclass} '
                         'groups, but additional fields are allowed')
            else:
                self.log(f'This field is not defined in {group.nxclass}',
                         level='warning')
        else:
            if '@deprecated' in tag:
                self.log(f'This field is now deprecated. {tag["@deprecated"]}',
                         level='warning')
            if field.exists():
                if '@type' in tag:  
                    self.check_type(field, tag['@type'])
                if 'dimensions' in tag:
                    self.check_dimensions(field, tag['dimensions'])
                if 'enumeration' in tag:
                    self.check_enumeration(field, tag['enumeration'])
                if 'attribute' in tag:
                    attributes = tag['attribute']
                else:
                    attributes = None
                if '@units' in tag:
                    units = tag['@units']
                else:
                    units = None
                self.check_attributes(field, attributes=attributes,
                                      units=units)
        self.output_log()


field_validator = FieldValidator()


class FileValidator(Validator):

    def __init__(self, filename, definitions=None):
        """
        Initializes a FileValidator instance.

        Parameters
        ----------
        filename : str
            The path to the NeXus file to validate.
        definitions : str, optional
            The path to the directory containing the NeXus base class
            definitions (default is None).
        """
        super().__init__(definitions=definitions)
        self.filepath = Path(filename).resolve()

    def validate(self, path=None):
        """
        Validates a NeXus file by walking through its tree structure.
        
        Each group is validated by its corresponding GroupValidator.

        Parameters
        ----------
        path : str, optional
            The path to the group to start validation from (default is
            None, which means the entire file will be validated).
        """
        with nxopen(self.filepath) as root:
            if path:
                parent_group = root[path]
            else:
                parent_group = root
            if not isinstance(parent_group, NXgroup):
                logger.error(f'{parent_group.nxpath} is not a NeXus group')
                return
            validator = get_validator(parent_group.nxclass,
                                      definitions=self.definitions)
            validator.validate(parent_group, parent=self)
        self.output_log()


def validate_file(filename, path=None, definitions=None):
    """
    Validates a NeXus file by walking through its tree structure.

    Each group is validated by its corresponding GroupValidator.

    Parameters
    ----------
    filename : str
        The path to the NeXus file to validate.
    path : str, optional
        The path to the group to start validation from (default is
        None, which means the entire file will be validated).
    definitions : str, optional
        The path to the directory containing the NeXus base class
        definitions (default is None).

    Returns
    -------
    tuple
        A tuple containing the total number of warnings and errors
        encountered while validating the file.
    """
    if not Path(filename).exists():
        logger.error(f'File "{filename}" does not exist')
        return
    if path is None:
        path = '/'

    try:
        validator = FileValidator(filename, definitions=definitions)
    except NeXusError as e:
        logger.error(e)
        return

    log_header(validator, filename=filename, path=path)

    validator.validate(path)

    return log_summary()


class ApplicationValidator(Validator):

    def __init__(self, application, definitions=None):
        """
        Initializes an ApplicationValidator instance.

        Parameters
        ----------
        application : str
            The name of the application definition to load.
        definitions : str, optional
            The path to the directory containing the NeXus base class
            definitions (default is None).
        """
        super().__init__(definitions=definitions)
        self.symbols = {}
        self.xml_dict = self.load_application(application)
        
    def load_application(self, application):
        """
        Loads an application definition from an XML file.

        Parameters
        ----------
        application : str, optional
            The name of the application to be loaded. If not provided,
            the application name stored in the instance will be used.

        Returns
        -------
        dict
            A dictionary representation of the application definition.
        """
        if Path(application).exists():
            app_path = Path(application).resolve()
        elif self.applications is not None:
            app_path = self.applications / (f'{application}.nxdl.xml')
            if not app_path.exists() and self.contributions is not None:
                app_path = self.contributions / (f'{application}.nxdl.xml') 
        elif self.contributions is not None:
            app_path = self.contributions / (f'{application}.nxdl.xml')
        else:
            app_path = None
        if app_path is not None and app_path.exists():
            tree = ET.parse(app_path)
        else:
            raise NeXusError(
                f'The application definition "{application}" does not exist')
        xml_root = tree.getroot()
        strip_namespace(xml_root)
        if xml_root.tag != 'definition':
            raise NeXusError(
                f'The application definition "{application}"'
                'does not contain the correct root tag.')
        symbols = xml_root.find('symbols')
        if symbols is not None:
            self.symbols.update(xml_to_dict(symbols)['symbol'])
        xml_dict = xml_to_dict(xml_root.find('group'))
        if xml_root.attrib['extends'] != 'NXobject':
            xml_extended_dict = self.load_application(
                xml_root.attrib['extends'])
            xml_dict = merge_dicts(xml_extended_dict, xml_dict)
        self.filepath = app_path.resolve()
        return xml_dict

    def validate_group(self, xml_dict, nxgroup, indent=0):
        """
        Validates a NeXus group against an XML definition.

        This function checks if the provided NeXus group matches the
        structure defined in the given XML dictionary. It recursively
        validates all subgroups and fields within the group, ensuring
        that the required components are present and correctly
        formatted.

        Parameters
        ----------
        xml_dict : dict
            The XML dictionary containing the definition of the group.
        nxgroup : NXgroup
            The NeXus group to be validated.
        indent : int, optional
            The current indentation level (default is 0).
        """
        self.indent = indent
        group_validator = get_validator(nxgroup.nxclass,
                                        definitions=self.definitions)
        group_validator.parent = self
        for key, value in xml_dict.items():
            if key == 'group':
                for group in value:
                    if '@minOccurs' in value[group]:
                        minOccurs = int(value[group]['@minOccurs'])
                    else:
                        minOccurs = 1
                    if '@type' in value[group]:
                        name = group
                        group = value[group]['@type']
                        self.log(f'Group: {name}: {group}', level='all',
                                 indent=self.indent)
                        nxgroups = [g for g in nxgroup.component(group)
                                    if g.nxname == name]
                    else:
                        name = None
                        self.log(f'Group: {group}', level='all',
                                 indent=self.indent)
                        nxgroups = nxgroup.component(group)
                    self.indent += 1
                    if len(nxgroups) < minOccurs:
                        self.log(
                            f'{len(nxgroups)} {group} group(s) '
                            f'are in the NeXus file.  At least {minOccurs} '
                            'are required', level='error')
                    elif minOccurs == 0:
                        self.log(
                            'This optional group is not in the NeXus file')
                    for i, nxsubgroup in enumerate(nxgroups):
                        if name:
                            if i != 0:
                                self.log(f'Group: {name}: {group}',
                                         level='all', indent=self.indent)
                            self.validate_group(
                                value[name], nxsubgroup, indent=self.indent)
                        else:
                            if i != 0:
                                self.log(f'Group: {group}', level='all',
                                         indent=self.indent)
                            self.validate_group(
                                value[group], nxsubgroup, indent=self.indent)
                    self.indent -= 1
                self.output_log()
            elif key == 'field' or key == 'link':
                for field in value:
                    if '@minOccurs' in value[field]:
                        minOccurs = int(value[field]['@minOccurs'])
                    else:
                        minOccurs = 1
                    if field in nxgroup.entries:
                        group_validator.symbols.update(self.symbols)
                        field_validator.validate(
                            value[field], nxgroup[field], link=(key=='link'),
                            parent=self, minOccurs=minOccurs,
                            indent=self.indent)
                    else:
                        field_path = nxgroup.nxpath + '/' + field
                        self.log(f'{key.capitalize()}: {field_path}',
                                 level='all')
                        self.indent += 1
                        if minOccurs > 0:
                            self.log(f'This required {key} is not '
                                     'in the NeXus file', level='error')
                        else:
                            self.log(f'This optional {key}) is not '
                                     'in the NeXus file')
                        self.indent -= 1
                self.output_log()
        group_validator.check_symbols(indent=self.indent)
        self.output_log()
    
    def validate(self, entry, level=None):
        """
        Validates a NeXus entry against an XML definition.

        This function checks if the provided NeXus entry matches the
        structure defined in the given XML dictionary. It recursively
        validates all subgroups and fields within the entry, ensuring
        that the required components are present and correctly
        formatted.

        Parameters
        ----------
        entry : object
            The NeXus entry to be validated.
        level : str, optional
            The logging level (default is None).
        """
        root = entry.nxroot
        nxpath = entry.nxpath
        if level is not None:
            logger.setLevel(get_log_level(level))
        self.validate_group(self.xml_dict, root[nxpath])
        self.output_log()


def validate_application(filename, path=None, application=None,
                         definitions=None):
    """
    Validates a NeXus entry against an application definition.

    This function checks if the provided NeXus entry matches the
    structure defined in the given application definition. It
    recursively validates all subgroups and fields within the entry,
    ensuring that the required components are present and correctly
    formatted.

    Parameters
    ----------
    filename : str
        The path to the NeXus file to validate.
    path : str, optional
        The path to the group to start validation from (default is
        None, which means the entire file will be validated).
    application : str, optional
        The name of the application definition to validate against
        (default is None).
    definitions : str, optional
        The path to the directory containing the NeXus base class
        definitions (default is None).

    Returns
    -------
    tuple
        A tuple containing the total number of warnings and errors
        encountered while validating the file.
    """
    with nxopen(filename) as root:
        if path is None:
            nxpath = root.NXentry[0].nxpath
        else:
            nxpath = path
        entry = root[nxpath]
        if not (isinstance(entry, NXentry) or isinstance(entry, NXsubentry)):
            logger.error(
                f'Path "{nxpath}" is not a NXentry or NXsubentry group')
            return
        elif application is None and 'definition' in entry:
            application = entry['definition'].nxvalue
        elif application is None:
            logger.error(f'No application definition is defined in "{nxpath}"')
            return

        try:
            validator = ApplicationValidator(application,
                                             definitions=definitions)
        except NeXusError as e:
            logger.error(e)
            return

        log_header(validator, filename, nxpath, application)

        validator.validate(entry)

    return log_summary()


def inspect_base_class(base_class, definitions=None):
    """
    Prints the valid components of a NeXus base class.

    Parameters
    ----------
    base_class : str
        The name of the NeXus base class to inspect.
    definitions : str or Path, optional
        The path to the directory containing the NeXus base class
        definitions (default is None).
    """
    logger.setLevel(logging.INFO)

    validator = get_validator(base_class, definitions=definitions)

    if validator.filepath is not None:
        log(f"\nValid components of the {base_class} base class")
        log(f"NXDL File: {truncate_path(validator.filepath)}\n")
    else:
        log(f'NXDL file for "{base_class}" does not exist')
        log(f"Definitions: {truncate_path(validator.filepath)}\n")
        return

    tree = ET.parse(validator.filepath)
    root = tree.getroot()
    strip_namespace(root)

    from pygments import highlight
    from pygments.lexers import XmlLexer
    from pygments.formatters import TerminalFormatter

    log(highlight(ET.tostring(root, encoding='unicode'), XmlLexer(),
                  TerminalFormatter()))


def log(message, level='info', indent=0):
    """
    Logs a message at a specified level with optional indentation.

    Parameters
    ----------
    message : str
        The message to be logged.
    level : str, optional
        The level of the log message (default is 'info').
    indent : int, optional
        The number of spaces to indent the log message (default is 0).
    """
    if level == 'info':
        logger.info(f'{4*indent*" "}{message}')
    elif level == 'debug':
        logger.log(logging.DEBUG, f'{4*indent*" "}{message}')
    elif level == 'warning':
        logger.warning(f'{4*indent*" "}{message}')
        logger.total['warning'] += 1
    elif level == 'error':
        logger.error(f'{4*indent*" "}{message}')
        logger.total['error'] += 1
    elif level == 'all':
        logger.critical(f'{4*indent*" "}{message}')


def log_header(validator, filename=None, path=None, application=None):  
    log("\n", level='all')
    if filename is not None:
        log(f"Filename: {filename}", level='all')
    if path is not None:
        log(f"Path: {path}", level='all')
    log(f"Definitions: {truncate_path(validator.definitions)}", level='all')
    if application and Path(application).exists():
        application = Path(application).stem[:-5]
    if application is not None:
        log(f"Application Definition: {application}", level='all')
        log(f"NXDL File: {truncate_path(validator.filepath)}", level='all')
    log("\n", level='all')
    logger.total = {'warning': 0, 'error': 0}


def log_summary():
    """
    Prints a summary of the total number of warnings and errors encountered
    during validation and returns the total counts.

    Returns
    -------
    tuple
        A tuple containing the total number of warnings and errors.
    """
    if logger.level <= logging.WARNING:
        log(f'\nTotal number of warnings: {logger.total["warning"]}',
            level='all')
        log(f'Total number of errors: {logger.total["error"]}\n', level='all')
    else:
        log(f'\nTotal number of errors: {logger.total["error"]}\n',
            level='all')
    
    return (logger.total['warning'], logger.total['error'])

