"""BusFactory class module."""
from typing import TypeVar

from qililab.platform.components.bus_driver import BusDriver

Element = TypeVar("Element", bound=BusDriver)


class BusFactory:
    """Hash table that loads a specific class given an object's __name__."""

    handlers: dict[str, type[BusDriver]] = {}

    @classmethod
    def register(cls, handler_cls: type[Element]) -> type[BusDriver]:
        """Register handler in the factory given the class (through its __name__).

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.__name__] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str) -> type[BusDriver]:
        """Return class attribute given its __name__"""
        return cls.handlers[name]
