"""InstrumentFactory class."""
from typing import TypeVar

from qcodes.instrument.instrument import Instrument

Element = TypeVar("Element", bound=Instrument)


class InstrumentDriverFactory:
    """Hash table that loads a specific class given an object's name."""

    handlers: dict[str, type[Instrument]] = {}

    @classmethod
    def register(cls, handler_cls: type[Element]) -> type[Instrument]:
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.__name__] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str) -> type[Instrument]:
        """Return class attribute."""
        return cls.handlers[name]
