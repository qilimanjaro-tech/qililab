"""BusFactory class module."""
from typing import TypeVar

from qililab.platform.components.interfaces.bus import BusInterface

Element = TypeVar("Element", bound=BusInterface)


class BusFactory:
    """Hash table that loads a specific class given an object's __name__."""

    handlers: dict[str, type[BusInterface]] = {}

    @classmethod
    def register(cls, handler_cls: type[Element]) -> type[BusInterface]:
        """Register handler in the factory given the class (through its __name__).

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.__name__] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str) -> type[BusInterface]:
        """Return class attribute given its __name__"""
        return cls.handlers[name]
