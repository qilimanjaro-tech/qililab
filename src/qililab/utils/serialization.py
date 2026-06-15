# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from io import StringIO
from pathlib import Path
from typing import Any, TypeVar, overload

from qililab.utils.safe_yaml import get_safe_loader
from qililab.yaml import yaml

T = TypeVar("T")


class SerializationError(Exception):
    """Custom exception for serialization errors."""


class DeserializationError(Exception):
    """Custom exception for deserialization errors."""


def serialize(obj: Any) -> str:
    """Serialize an object to a YAML string.

    Args:
        obj (Any): The object to serialize.

    Raises:
        SerializationError: If serialization fails.

    Returns:
        str: The serialized YAML string.
    """
    try:
        with StringIO() as stream:
            yaml.dump(obj, stream)
            return stream.getvalue()
    except Exception as e:
        raise SerializationError(f"Failed to serialize object {e}") from e


def serialize_to(obj: Any, file: str) -> None:
    """Serialize an object to a YAML file.

    Args:
        obj (Any): The object to serialize.
        file (str): The file path where the YAML data will be written.

    Raises:
        SerializationError: If serialization to file fails.
    """
    try:
        yaml.dump(obj, Path(file))
    except Exception as e:
        raise SerializationError(f"Failed to serialize object {e} to file {file}") from e


@overload
def deserialize(string: str) -> Any: ...


@overload
def deserialize(string: str, cls: type[T]) -> T: ...


def deserialize(string: str, cls: type[T] | None = None, trust_code: bool = False) -> Any | T:
    """Deserialize a YAML string to an object.

    By default the input is loaded with a registry-isolated, data-only loader that rejects
    code-execution YAML tags (``!!python/object/apply``, ``!function``, ``!lambda``, ...),
    so deserializing an untrusted string cannot execute arbitrary code. The ``cls`` type
    check still runs after loading.

    Args:
        string (str): The YAML string to deserialize.
        cls (type[T], optional): The class type to cast the deserialized object to. Defaults to None.
        trust_code (bool, optional): If True, load with the unsafe loader, allowing
            code-execution tags. Only use for input from a fully trusted source. Defaults to False.

    Raises:
        DeserializationError: If deserialization fails or the resulting object is not of the specified type.

    Returns:
        Any | T: The deserialized object, optionally cast to the specified class type.
    """
    loader = yaml if trust_code else get_safe_loader()
    try:
        with StringIO(string) as stream:
            result = loader.load(stream)
    except Exception as e:
        raise DeserializationError(f"Failed to deserialize YAML string: {e}") from e
    if cls is not None and not isinstance(result, cls):
        raise DeserializationError(f"Deserialized object is not of type {cls.__name__}")
    return result


@overload
def deserialize_from(file: str) -> Any: ...


@overload
def deserialize_from(file: str, cls: type[T]) -> T: ...


def deserialize_from(file: str, cls: type[T] | None = None, trust_code: bool = False) -> Any | T:
    """Deserialize a YAML file to an object.

    By default the file is loaded with a registry-isolated, data-only loader that rejects
    code-execution YAML tags (``!!python/object/apply``, ``!function``, ``!lambda``, ...),
    so deserializing an untrusted file cannot execute arbitrary code. The ``cls`` type
    check still runs after loading.

    Args:
        file (str): The file path of the YAML file to deserialize.
        cls (type[T], optional): The class type to cast the deserialized object to. Defaults to None.
        trust_code (bool, optional): If True, load with the unsafe loader, allowing
            code-execution tags. Only use for files from a fully trusted source. Defaults to False.

    Raises:
        DeserializationError: If deserialization fails or the resulting object is not of the specified type.

    Returns:
        Any | T: The deserialized object, optionally cast to the specified class type.
    """
    loader = yaml if trust_code else get_safe_loader()
    try:
        result = loader.load(Path(file))
    except Exception as e:
        raise DeserializationError(f"Failed to deserialize YAML string {e} from file {file}") from e
    if cls is not None and not isinstance(result, cls):
        raise DeserializationError(f"Deserialized object is not of type {cls.__name__}")
    return result
