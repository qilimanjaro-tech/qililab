"""InstrumentInterfaceFactory class module."""
from typing import TypeVar

from qililab.typings.factory_element import InstrumentFactoryElement

Element = TypeVar("Element", bound=InstrumentFactoryElement)


class InstrumentInterfaceFactory:
    """Hash table that loads a specific class given an object's __name__."""

    handlers: dict[str, type[InstrumentFactoryElement]] = {}

    @classmethod
    def register(cls, handler_cls: type[Element]) -> type[InstrumentFactoryElement]:
        """Register handler in the factory given the class (through its __name__).

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.__name__] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str) -> type[InstrumentFactoryElement]:
        """Return class attribute given its __name__"""
        return cls.handlers[name]
