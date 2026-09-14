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


def test_np_scalar_serialization_does_not_use_legacy_tag():
    """Test that numpy scalars serialized today no longer use the legacy '!np_scalar' tag."""
    assert "!np_scalar" not in dump_to_string({"value": np.float32(1.5)})


@pytest.mark.parametrize(
    ("scalar", "equivalent"),
    [
        (np.float64(1.5), 1.5),
        (np.float32(1.5), 1.5),
        (np.int64(7), 7),
        (np.int32(-3), -3),
        (np.uint8(255), 255),
        (np.bool_(True), True),
        (np.str_("hi"), "hi"),
        (np.float64("nan"), float("nan")),
        (np.float64("inf"), float("inf")),
        (np.float64("-inf"), float("-inf")),
    ],
)
def test_np_scalar_serializes_like_a_plain_python_scalar(scalar, equivalent):
    """Test that numpy scalars serialize byte for byte like their plain Python equivalents."""
    assert dump_to_string(scalar) == dump_to_string(equivalent)


def test_np_scalars_serialize_to_a_plain_yaml_document():
    """Test the document produced for a mapping holding numpy scalars, tags and all."""
    original = {"frequency": np.float64(5.2e9), "index": np.int64(3), "enabled": np.bool_(False)}

    assert dump_to_string(original) == "{enabled: false, frequency: 5200000000.0, index: 3}\n"


@pytest.mark.parametrize(
    ("scalar", "expected"),
    [(np.float64(1.5), 1.5), (np.float32(1.5), 1.5), (np.int64(7), 7), (np.int32(-3), -3), (np.uint8(255), 255)],
)
def test_np_numeric_scalar_round_trip_preserves_value_but_not_dtype(scalar, expected):
    """Test that a round trip returns the plain Python equivalent of a numeric numpy scalar.

    An untagged scalar carries no dtype, so dropping it is the intended trade-off: runcards and
    qprograms hold physical parameters whose numpy dtype is incidental.
    """
    loaded_scalar = yaml.load(dump_to_string({"value": scalar}))["value"]

    assert loaded_scalar == pytest.approx(expected)
    assert type(loaded_scalar) is type(expected)
    assert not isinstance(loaded_scalar, np.generic)


@pytest.mark.parametrize(
    ("scalar", "expected"), [(np.bool_(True), True), (np.bool_(False), False), (np.str_("hi"), "hi")]
)
def test_np_non_numeric_scalar_round_trip_preserves_value_but_not_dtype(scalar, expected):
    """Test that a round trip returns the plain Python equivalent of a boolean or string numpy scalar."""
    loaded_scalar = yaml.load(dump_to_string({"value": scalar}))["value"]

    assert loaded_scalar == expected
    assert type(loaded_scalar) is type(expected)
    assert not isinstance(loaded_scalar, np.generic)


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
