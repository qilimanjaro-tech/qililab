from abc import abstractmethod

from .base_instrument import BaseInstrument
from .instrument_interface_factory import InstrumentInterfaceFactory


@InstrumentInterfaceFactory.register
class LocalOscillator(BaseInstrument):
    """Interface of a local oscillator."""

    @abstractmethod
    def on(self) -> None:
        """Start RF output"""

    @abstractmethod
    def off(self) -> None:
        """Stop RF outout"""
