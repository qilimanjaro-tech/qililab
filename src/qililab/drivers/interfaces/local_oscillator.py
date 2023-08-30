from abc import abstractmethod

from qililab.typings.factory_element import FactoryElement

from .base_instrument import BaseInstrument
from .instrument_interface_factory import InstrumentInterfaceFactory


@InstrumentInterfaceFactory.register
class LocalOscillator(BaseInstrument, FactoryElement):
    """Interface of a local oscillator."""

    @abstractmethod
    def on(self) -> None:
        """Start RF output"""

    @abstractmethod
    def off(self) -> None:
        """Stop RF outout"""
