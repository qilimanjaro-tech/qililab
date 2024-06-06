from io import StringIO
from typing import Any, TypeVar, overload

from qililab.yaml import yaml

T = TypeVar("T")


class SerializationError(Exception):
    """Custom exception for serialization errors."""

    pass


class DeserializationError(Exception):
    """Custom exception for deserialization errors."""

    pass


def serialize(obj: Any) -> str:
    try:
        with StringIO() as stream:
            yaml.dump(obj, stream)
            result = stream.getvalue()
        return result
    except Exception as e:
        raise SerializationError(f"Failed to serialize object: {e}") from e


@overload
def deserialize(string: str) -> Any:
    ...


@overload
def deserialize(string: str, cls: type[T]) -> T:
    ...


def deserialize(string: str, cls: type[T] | None = None) -> Any | T:
    try:
        with StringIO(string) as stream:
            result = yaml.load(stream)
    except Exception as e:
        raise DeserializationError(f"Failed to deserialize YAML string: {e}") from e
    if cls is not None:
        if not isinstance(result, cls):
            raise TypeError(f"Deserialized object is not of type {cls.__name__}")
        return result
    return result


def _get_registered_classes(yaml_instance):
    representers = yaml_instance.representer.yaml_representers
    constructors = yaml_instance.constructor.yaml_constructors

    registered_classes = []

    # Inspect representers
    for tag, representer in representers.items():
        if hasattr(representer, "__self__"):
            cls = representer.__self__
            if cls not in registered_classes:
                registered_classes.append(cls)

    # Inspect constructors
    for tag, constructor in constructors.items():
        if hasattr(constructor, "__self__"):
            cls = constructor.__self__
            if cls not in registered_classes:
                registered_classes.append(cls)

    return registered_classes
