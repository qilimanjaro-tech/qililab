"""Class used as hashtable to load the class corresponding to a given category"""
from enum import Enum
from typing import Type, TypeVar

from qililab.typings.factory_element import FactoryElement

Element = TypeVar("Element", bound=FactoryElement)


class Factory:
    """Hash table that loads a specific class given an object's name."""

    handlers: dict[str, Type[FactoryElement]] = {}

    @classmethod
    def register(cls, handler_cls: Type[Element]):
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.name.value] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str | Enum):
        """Return class attribute."""
        return cls.handlers[name.value] if isinstance(name, Enum) else cls.handlers[name]
