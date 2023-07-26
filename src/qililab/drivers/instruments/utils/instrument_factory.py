"""InstrumentFactory class."""
from typing import TypeVar

from qcodes.instrument.instrument import Instrument

from qililab.typings.enums import InstrumentDriverName

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
        cls.handlers[handler_cls.name.value] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str | InstrumentDriverName) -> type[Instrument]:
        """Return class attribute."""
        return cls.handlers[name.value] if isinstance(name, InstrumentDriverName) else cls.handlers[name]
