"""InstrumentFactory class."""
from typing import TypeVar

from qililab.typings.enums import InstrumentDriverName
from qililab.typings.factory_element import FactoryElement

Element = TypeVar("Element", bound=FactoryElement)


class InstrumentDriverFactory:
    """Hash table that loads a specific class given an object's name."""

    handlers: dict[str, type[FactoryElement]] = {}

    @classmethod
    def register(cls, handler_cls: type[Element]) -> type[FactoryElement]:
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.name.value] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str | InstrumentDriverName) -> type[FactoryElement]:
        """Return class attribute."""
        return cls.handlers[name.value] if isinstance(name, InstrumentDriverName) else cls.handlers[name]
