import xml.etree.ElementTree as ET
from types import SimpleNamespace

import numpy as np
import pytest

from nexusformat.nexus import NeXusError, NXfield
from nexusformat.nexus.utils import xml_to_dict
from nexusformat.nexus.validate import (ApplicationValidator, FieldValidator,
                                        GroupValidator)


def get_dimensions(required=None):
    required_attribute = '' if required is None else f' required="{required}"'
    xml = f'''<field>
        <dimensions rank="dataRank">
            <dim index="1" value="nP"/>
            <dim index="2" value="i"/>
            <dim index="3" value="j"/>
            <dim index="4" value="k"{required_attribute}/>
        </dimensions>
    </field>'''
    return xml_to_dict(ET.fromstring(xml))['dimensions']


def validate_dimensions(dimensions):
    validator = FieldValidator()
    validator.parent = SimpleNamespace(
        symbols={symbol: {} for symbol in ('dataRank', 'nP', 'i', 'j', 'k')})
    validator.check_dimensions(
        NXfield(np.zeros((2, 3, 4)), name='data'), dimensions)
    return [message for message, _, _ in validator.logged_messages]


def test_xml_to_dict_preserves_optional_dimensions():
    dimensions = get_dimensions(required='false')

    assert dimensions['dim'][4] == 'k'
    assert dimensions['required'][4] == 'false'


@pytest.mark.parametrize('required', ['false', '0'])
def test_optional_trailing_dimension_can_be_absent(required):
    messages = validate_dimensions(get_dimensions(required=required))

    assert not any('dimension index of "k" = 4' in message
                   for message in messages)


@pytest.mark.parametrize('required', [None, 'true', '1'])
def test_required_trailing_dimension_is_still_reported(required):
    messages = validate_dimensions(get_dimensions(required=required))

    assert any('dimension index of "k" = 4' in message
               for message in messages)


DEFINITION = '<definition xmlns="http://definition.nexusformat.org/nxdl/3.1" '\
             'name="{name}" {attributes}>{content}</definition>'


@pytest.fixture
def definitions(tmp_path):
    (tmp_path / 'base_classes').mkdir()
    (tmp_path / 'applications').mkdir()
    write_nxdl(tmp_path, 'NXobject', attributes='')
    return tmp_path


def write_nxdl(definitions, name, content='', folder='base_classes',
               attributes='extends="NXobject"'):
    (definitions / folder / f'{name}.nxdl.xml').write_text(
        DEFINITION.format(name=name, attributes=attributes, content=content))


@pytest.mark.parametrize('content', [
    '<enumeration><item/></enumeration>',
    '<field name="a"><dimensions><dim index="x" value="n"/></dimensions>'
    '</field>',
    '<symbols/>',
    '<field units="NX_LENGTH"/>',
    '<attribute/>',
    '<group/>'])
def test_malformed_base_class_does_not_raise(definitions, content):
    write_nxdl(definitions, 'NXtest', content=content)

    validator = GroupValidator('NXtest', definitions=definitions)

    assert validator.valid_class


def test_unnamed_field_is_reported(definitions):
    write_nxdl(definitions, 'NXtest', content='<field units="NX_LENGTH"/>')

    validator = GroupValidator('NXtest', definitions=definitions)

    assert validator.valid_fields == {}
    assert any(level == 'error' for _, level, _ in validator.logged_messages)


def test_syntax_error_in_base_class_raises_nexus_error(definitions):
    (definitions / 'base_classes' / 'NXtest.nxdl.xml').write_text('<definition')

    with pytest.raises(NeXusError):
        GroupValidator('NXtest', definitions=definitions)


def test_wrong_root_tag_raises_nexus_error(definitions):
    (definitions / 'base_classes' / 'NXtest.nxdl.xml').write_text('<other/>')

    with pytest.raises(NeXusError):
        GroupValidator('NXtest', definitions=definitions)


def test_missing_parent_class_raises_nexus_error(definitions):
    write_nxdl(definitions, 'NXtest', attributes='extends="NXmissing"')

    with pytest.raises(NeXusError):
        GroupValidator('NXtest', definitions=definitions)


def test_circular_extends_raises_nexus_error(definitions):
    write_nxdl(definitions, 'NXa', attributes='extends="NXb"')
    write_nxdl(definitions, 'NXb', attributes='extends="NXa"')
    write_nxdl(definitions, 'NXself', attributes='extends="NXself"')

    with pytest.raises(NeXusError):
        GroupValidator('NXa', definitions=definitions)
    with pytest.raises(NeXusError):
        GroupValidator('NXself', definitions=definitions)


def test_ignore_extra_false_is_not_true(definitions):
    write_nxdl(definitions, 'NXtest',
               attributes='extends="NXobject" ignoreExtraFields="false" '
                          'ignoreExtraGroups="true"')

    validator = GroupValidator('NXtest', definitions=definitions)

    assert not validator.ignoreExtraFields
    assert validator.ignoreExtraGroups


def test_unknown_class_has_ignore_flags(definitions):
    validator = GroupValidator('NXmissing', definitions=definitions)

    assert not validator.valid_class
    assert validator.ignoreExtraGroups is False


@pytest.mark.parametrize('content, attributes', [
    ('<symbols/>', 'extends="NXobject"'),
    ('<group type="NXentry"/>', ''),
    ('<group type="NXentry"/>', 'extends="NXmissing"')])
def test_application_without_group_or_bad_extends(definitions, content,
                                                  attributes):
    write_nxdl(definitions, 'NXapp', content=content, folder='applications',
               attributes=attributes)
    if 'group' in content and not attributes:
        assert ApplicationValidator('NXapp', definitions=definitions)
    else:
        with pytest.raises(NeXusError):
            ApplicationValidator('NXapp', definitions=definitions)


def test_application_circular_extends(definitions):
    for name, parent in (('NXapp1', 'NXapp2'), ('NXapp2', 'NXapp1')):
        write_nxdl(definitions, name, content='<group type="NXentry"/>',
                   folder='applications', attributes=f'extends="{parent}"')

    with pytest.raises(NeXusError):
        ApplicationValidator('NXapp1', definitions=definitions)


def test_application_syntax_error(definitions):
    (definitions / 'applications' / 'NXapp.nxdl.xml').write_text('<definition')

    with pytest.raises(NeXusError):
        ApplicationValidator('NXapp', definitions=definitions)


def test_non_integer_min_occurs_is_ignored():
    validator = FieldValidator()

    validator.check_occurrences(
        'field', {'@minOccurs': 'unbounded'}, 0)

    assert validator.logged_messages[0][1] == 'error'


def test_enumeration_with_array_value():
    validator = FieldValidator()

    validator.check_enumeration(NXfield(np.arange(3), name='a'), ['x', 'y'])

    assert validator.logged_messages[0][1] == 'error'


def test_last_dimension_size_is_checked():
    validator = FieldValidator()
    dimensions = xml_to_dict(ET.fromstring(
        '<field><dimensions><dim index="2" value="3"/></dimensions></field>')
    )['dimensions']
    validator.parent = SimpleNamespace(symbols={})

    validator.check_dimensions(NXfield(np.zeros((2, 3)), name='data'),
                               dimensions)

    assert [m for m, _, _ in validator.logged_messages] == [
        'The field has the correct size of 3']


def test_xml_to_dict_tolerates_malformed_items():
    element = ET.fromstring(
        '<field><enumeration><item/><item value="a"/></enumeration>'
        '<dimensions><dim index="x" value="n"/></dimensions></field>')

    result = xml_to_dict(element)

    assert result['enumeration'] == ['a']
    assert result['dimensions']['dim'] == {}
