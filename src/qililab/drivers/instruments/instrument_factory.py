"""InstrumentDriverFactory class module."""
from abc import (  # The ABC is actually a BaseInstrument class, less general, but we don't want to cause circular imports.
    ABC,
)
from typing import TypeVar

Element = TypeVar("Element", bound=ABC)  # The ABC is actually a BaseInstrument class.


class InstrumentDriverFactory:
    """Hash table that loads a specific instrument driver (child of BaseInstrument) given an object's __name__.

    (Actually this factory could initialize any class that inherits from ABC which gets registered into it with @InstrumentDriverFactory.register)
    """

    handlers: dict[str, type[ABC]] = {}  # The ABC is actually a BaseInstrument class.

    @classmethod
    def register(cls, handler_cls: type[Element]) -> type[ABC]:  # The ABC is actually a BaseInstrument class.
        """Register handler in the factory given the class (through its __name__).

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.__name__] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str) -> type[ABC]:  # The ABC is actually a BaseInstrument class.
        """Return class attribute given its __name__"""
        return cls.handlers[name]
