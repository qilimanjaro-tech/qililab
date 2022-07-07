"""InstrumentFactory class."""
from typing import Dict, Type, TypeVar

from qililab.instrument_controllers import InstrumentController

Element = TypeVar("Element", bound=InstrumentController)


class InstrumentControllerFactory:
    """Hash table that loads a specific class given an object's name."""

    handlers: Dict[str, Type[InstrumentController]] = {}

    @classmethod
    def register(cls, handler_cls: Type[Element]) -> Type[InstrumentController]:
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.handlers[handler_cls.name.value] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str) -> Type[InstrumentController]:
        """Return class attribute."""
        return cls.handlers[name]
