import io
import types
from collections import deque
from uuid import UUID

import numpy as np

from qililab.yaml import yaml


def test_ndarray_serialization():
    """Test serialization and deserialization of numpy ndarray."""
    # Create a sample ndarray
    original_array = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)

    # Dump the array to YAML
    stream = io.StringIO()
    yaml.dump(original_array, stream)
    yaml_str = stream.getvalue()

    # Load the array back from YAML
    loaded_array = yaml.load(yaml_str)

    # Verify that the original and loaded arrays are equal
    np.testing.assert_array_equal(original_array, loaded_array)


def test_deque_serialization():
    """Test serialization and deserialization of deque."""
    # Create a sample deque
    original_deque = deque([1, 2, 3, 4, 5])

    # Dump the deque to YAML
    stream = io.StringIO()
    yaml.dump(original_deque, stream)
    yaml_str = stream.getvalue()

    # Load the deque back from YAML
    loaded_deque = yaml.load(yaml_str)

    # Verify that the original and loaded deques are equal
    assert original_deque == loaded_deque
    assert isinstance(loaded_deque, deque)


def test_lambda_serialization():
    """Test serialization and deserialization of a lambda function."""

    def another_function(y):
        return y + 1

    # Define a sample lambda function
    def original_lambda(x, y):
        return x + another_function(y)

    # Dump the lambda function to YAML
    stream = io.StringIO()
    yaml.dump(original_lambda, stream)
    yaml_str = stream.getvalue()

    # Load the lambda function back from YAML
    loaded_lambda = yaml.load(yaml_str)

    # Verify that the loaded object is a function
    assert isinstance(loaded_lambda, types.FunctionType)

    # Test that the loaded lambda behaves the same as the original
    x, y = 5, 10
    assert original_lambda(x, y) == loaded_lambda(x, y)


def test_uuid_serialization():
    """Test serialization and deserialization of UUID."""
    # Create a sample UUID
    original_uuid = UUID("12345678123456781234567812345678")

    # Dump the UUID to YAML
    stream = io.StringIO()
    yaml.dump(original_uuid, stream)
    yaml_str = stream.getvalue()

    # Load the UUID back from YAML
    loaded_uuid = yaml.load(yaml_str)

    # Verify that the original and loaded UUIDs are equal
    assert original_uuid == loaded_uuid
    assert isinstance(loaded_uuid, UUID)


def test_legacy_tuple_deserialization():
    """Test deserialization of the '!tuple' tag used by qililab versions that depended on qilisdk."""
    # Files serialized before qilisdk was removed as a dependency may still contain this tag.
    yaml_str = "!tuple [1, 2, 3]\n"

    loaded_tuple = yaml.load(yaml_str)

    # Verify that the loaded object is a tuple with the expected values
    assert loaded_tuple == (1, 2, 3)
    assert isinstance(loaded_tuple, tuple)


def test_tuple_serialization_does_not_use_legacy_tag():
    """Test that tuples serialized today no longer use the legacy '!tuple' tag."""
    original_tuple = (1, 2, 3)

    # Dump the tuple to YAML
    stream = io.StringIO()
    yaml.dump(original_tuple, stream)
    yaml_str = stream.getvalue()

    # Verify that the legacy tag is not used
    assert "!tuple" not in yaml_str

    # Load the tuple back from YAML
    loaded_tuple = yaml.load(yaml_str)

    # Verify that the original and loaded tuples are equal
    assert original_tuple == loaded_tuple
    assert isinstance(loaded_tuple, tuple)
