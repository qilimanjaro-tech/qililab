"""Class used as hashtable to load the class corresponding to a given category"""
from typing import Dict, Type, TypeVar

from qililab.typings import BusElement

Element = TypeVar("Element", bound=BusElement)


class BusElementFactory:
    """Hash table that loads a specific class given an object's name."""

    handlers: Dict[str, Type[BusElement]] = {}

    @classmethod
    def register(cls, handler_cls: Type[Element]):
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.name.value] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str):
        """Return class attribute."""
        return cls.handlers[name]
