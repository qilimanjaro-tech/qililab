"""BusFactory class module."""
from abc import ABC
from typing import TypeVar

Element = TypeVar("Element", bound=ABC)


class BusFactory:
    """Hash table that loads a specific class given an object's __name__."""

    handlers: dict[str, type[ABC]] = {}

    @classmethod
    def register(cls, handler_cls: type[Element]) -> type[ABC]:
        """Register handler in the factory given the class (through its __name__).

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.__name__] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str) -> type[ABC]:
        """Return class attribute given its __name__"""
        return cls.handlers[name]
