import io
import types
from collections import deque
from uuid import UUID

import numpy as np
import pytest

from qililab.yaml import yaml
from tests.test_utils import compare_objects


def dump_to_string(obj) -> str:
    """Serialize an object and return the resulting YAML document."""
    stream = io.StringIO()
    yaml.dump(obj, stream)
    return stream.getvalue()


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


@pytest.mark.parametrize(
    ("dtype", "value"),
    [("float64", 1.5), ("float32", 1.5), ("int64", 7), ("int32", -3), ("uint8", 255), ("bool", True)],
)
def test_legacy_np_scalar_deserialization(dtype, value):
    """Test deserialization of the '!np_scalar' tag used by qililab versions that depended on qilisdk."""
    # Files serialized before qilisdk was removed as a dependency may still contain this tag.
    yaml_str = f"!np_scalar {{dtype: {dtype}, value: {value}}}\n"

    loaded_scalar = yaml.load(yaml_str)

    # The legacy tag carries the dtype, so deserialization restores the numpy scalar faithfully.
    assert isinstance(loaded_scalar, np.generic)
    assert loaded_scalar.dtype == np.dtype(dtype)
    assert loaded_scalar == np.dtype(dtype).type(value)


def test_np_float32_round_trip_is_exact_when_recast():
    """Test that a float32 widened to float64 by serialization recasts back without loss."""
    original_scalar = np.float32(0.1)

    loaded_scalar = yaml.load(dump_to_string({"value": original_scalar}))["value"]

    assert loaded_scalar == pytest.approx(float(original_scalar))
    assert np.float32(loaded_scalar) == original_scalar


def test_ndarray_serialization_is_unaffected_by_np_scalar_representer():
    """Test that arrays keep the '!ndarray' tag, since np.ndarray is not an np.generic subclass."""
    original_array = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)

    yaml_str = dump_to_string(original_array)
    assert "!ndarray" in yaml_str

    loaded_array = yaml.load(yaml_str)

    is_equal, differences = compare_objects(loaded_array, original_array)
    assert is_equal, "\n".join(differences)
