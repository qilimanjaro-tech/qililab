"""Class used as hashtable to load the class corresponding to a given category"""
from typing import Dict, Type

from qililab.typings import BusElement


class BusElementFactory:
    """Hash table that loads a specific class given an object's name."""

    bus_element_handlers: Dict[str, Type[BusElement]] = {}

    @classmethod
    def register(cls, handler_cls: Type[BusElement]):
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.bus_element_handlers[handler_cls.name.value] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str):
        """Return class attribute."""
        return cls.bus_element_handlers[name]
