import xml.etree.ElementTree as ET
from types import SimpleNamespace

import numpy as np
import pytest

from nexusformat.nexus import NXfield
from nexusformat.nexus.utils import xml_to_dict
from nexusformat.nexus.validate import FieldValidator


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
