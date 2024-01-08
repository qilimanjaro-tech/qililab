from dataclasses import fields, is_dataclass
from typing import Any, Protocol, Type, TypedDict, TypeVar, _ProtocolMeta, cast, runtime_checkable

T = TypeVar("T", bound="DictSerializable")


class DictSerializableObject(TypedDict):
    """Typed dictionary describing a serialized object."""

    type: str
    attributes: dict[str, Any]


def is_dict_serializable_object(obj: Any) -> bool:
    """Check if the object follows the schema of `DictSerializableObject` typed dictionary.

    Args:
        obj (Any): The object to check

    Returns:
        bool: True, if object follows the schema of `DictSerializableObject` typed dictionary.
    """
    if not isinstance(obj, dict):
        return False

    if "type" not in obj or not isinstance(obj["type"], str):
        return False

    if "attributes" not in obj or not isinstance(obj["attributes"], dict):
        return False

    return all(isinstance(key, str) for key in obj["attributes"])


class DictSerializableFactory:
    """Factory to store information of `DictSerializable` classes."""

    _registry: dict[str, Type["DictSerializable"]] = {}

    @classmethod
    def register(cls, name: str, dict_serializable_class: Type["DictSerializable"]) -> None:
        """Register class."""
        cls._registry[name] = dict_serializable_class

    @classmethod
    def get(cls, name: str) -> Type["DictSerializable"]:
        """Get class by name."""
        if name not in cls._registry:
            raise ValueError(f"'{name}' is not a class that can be (de)serialized (from)to dictionary.")
        return cls._registry[name]


class DictSerializableMeta(_ProtocolMeta):
    """Metaclass to be used in `DictSerializable` protocol. Automatically registers any `DictSerializable` class to `DictSerializableFactory`."""

    def __new__(
        mcs: Type["DictSerializableMeta"], name: str, bases: tuple, namespace: dict[str, Any]
    ) -> Type["DictSerializable"]:
        new_class = super().__new__(mcs, name, bases, namespace)
        new_class = cast(Type["DictSerializable"], new_class)
        if bases != (object,):  # Avoid registering the base DictSerializable protocol
            DictSerializableFactory.register(name, new_class)
        return new_class


@runtime_checkable
class DictSerializable(Protocol, metaclass=DictSerializableMeta):
    """A protocol that defines a serializable object which can be converted to and from a dictionary.

    This protocol is used to ensure that objects conforming to it can be serialized into a dictionary
    format and deserialized back into an object. It is particularly useful for objects that need to be
    easily converted to a format that can be JSON-serialized.

    Methods:
        to_dict: Converts the object into a dictionary format.
        from_dict: Creates an instance of the object from a dictionary.
    """

    def to_dict(self) -> DictSerializableObject:
        """Converts the object into a dictionary format.

        Returns:
            DictSerializableObject: A typed dictionary representing the serialized state of the object.
        """

        def process_element(element):
            if isinstance(element, DictSerializable):
                return element.to_dict()
            elif isinstance(element, list):
                return [process_element(item) for item in element]
            elif isinstance(element, tuple):
                return tuple(process_element(item) for item in element)
            elif isinstance(element, set):
                return {process_element(item) for item in element}
            else:
                return element

        attributes = {k: process_element(v) for k, v in vars(self).items()}

        return {"type": self.__class__.__name__, "attributes": attributes}

    @classmethod
    def from_dict(cls: Type[T], data: dict[str, Any]) -> T:
        """Creates an instance of the object from a dictionary.

        Args:
            data (dict[str, Any]): A dictionary containing the serialized state of the object.

        Returns:
            T: An instance of the object populated with data from the dictionary.
        """

        def process_attribute(attribute):
            if is_dict_serializable_object(attribute):
                return from_dict(attribute)
            if isinstance(attribute, list):
                return [process_attribute(item) for item in attribute]
            if isinstance(attribute, tuple):
                return tuple(process_attribute(item) for item in attribute)
            if isinstance(attribute, set):
                return {process_attribute(item) for item in attribute}
            return attribute

        if is_dataclass(cls):
            # Create an instance with only the init-able fields
            init_fields = {f.name: process_attribute(data[f.name]) for f in fields(cls) if f.init}
            dataclass_instance = cls(**init_fields)

            # Check if the dataclass is frozen
            is_frozen = getattr(cls, "__dataclass_params__").frozen

            # Set non-init fields
            for f in fields(cls):
                if not f.init and f.name in data:
                    processed_value = process_attribute(data[f.name])
                    if is_frozen:
                        object.__setattr__(dataclass_instance, f.name, processed_value)
                    else:
                        setattr(dataclass_instance, f.name, processed_value)

            instance = cast(T, dataclass_instance)
        else:
            instance = cls.__new__(cls)
            for key, value in data.items():
                processed_value = process_attribute(value)
                setattr(instance, key, processed_value)

        return instance


def from_dict(dictionary: DictSerializableObject):
    """Constructs an object instance conforming to the `DictSerializable` protocol from a dictionary.

    This function is a utility to deserialize a dictionary into an object that conforms to the
    `DictSerializable` protocol. It is typically used to convert data from JSON or similar formats
    back into complex Python objects.

    Args:
        dictionary (DictSerializableObject): A dictionary representing the serialized state of a DictSerializable object, containing a `type` key to identify the object class and an `attributes` key with its serialized attributes.

    Returns:
        DictSerializable: An instance of the class identified in the dictionary, populated with the provided attributes.
    """
    cls_name = dictionary["type"]
    cls_attributes = dictionary["attributes"]
    cls = DictSerializableFactory.get(cls_name)
    return cls.from_dict(cls_attributes)
