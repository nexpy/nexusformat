import os

import pytest
from nexusformat.nexus import NXfield, NXentry, nxopen

def test_encoding_detection(tmpdir):
    
    filename = os.path.join(tmpdir, "encoding_test.nxs")

    latin1_text = "Café"
    encoded_bytes = latin1_text.encode('latin-1')

    with nxopen(filename, 'w') as root:
        root['entry'] = NXentry()
        root['entry/name'] = NXfield(encoded_bytes, dtype='S')

    with nxopen(filename, 'r') as root:
        retrieved_bytes = root['entry/name'].nxvalue

    if isinstance(retrieved_bytes, bytes):
        decoded_text = retrieved_bytes.decode('latin-1')
        assert decoded_text == latin1_text
        with pytest.raises(UnicodeDecodeError):
            retrieved_bytes.decode('utf-8')
    else:
        assert str(retrieved_bytes) == latin1_text


@pytest.mark.parametrize("encoding", ["latin-1", "cp1252", "ascii"])
def test_multiple_encodings(tmpdir, encoding):

    filename = os.path.join(tmpdir, f"test_{encoding}.nxs")
    original_text = "Test_Data"

    with nxopen(filename, 'w') as root:
        root['entry'] = NXentry()
        root['entry/name'] = NXfield(original_text.encode(encoding), dtype='S')

    with nxopen(filename, 'r') as root:
        value = root['entry/name'].nxvalue

    if isinstance(value, bytes):
        assert value.decode(encoding) == original_text
    else:
        assert str(value) == original_text
