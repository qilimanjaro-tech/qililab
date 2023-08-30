"""Generic interface for a Digitiser."""
from abc import abstractmethod
from typing import Any

from qililab.typings.factory_element import FactoryElement

from .base_instrument import BaseInstrument
from .instrument_interface_factory import InstrumentInterfaceFactory


@InstrumentInterfaceFactory.register
class Digitiser(BaseInstrument, FactoryElement):
    """Digitiser interface."""

    @abstractmethod
    def get_results(self) -> Any:
        """Get the acquisition results."""
