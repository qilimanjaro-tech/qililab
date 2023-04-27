"""InstrumentFactory class."""
from typing import Type, TypeVar

from qililab.instruments.instrument import Instrument
from qililab.typings.enums import InstrumentName

Element = TypeVar("Element", bound=Instrument)


class InstrumentFactory:
    """Hash table that loads a specific class given an object's name."""

    handlers: dict[str, Type[Instrument]] = {}

    @classmethod
    def register(cls, handler_cls: Type[Element]) -> Type[Instrument]:
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.name.value] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str | InstrumentName) -> Type[Instrument]:
        """Return class attribute."""
        return cls.handlers[name.value] if isinstance(name, InstrumentName) else cls.handlers[name]
