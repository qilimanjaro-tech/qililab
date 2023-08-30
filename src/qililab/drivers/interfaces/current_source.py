""" Module containing the interface for the current_sources """
from abc import abstractmethod

from .base_instrument import BaseInstrument
from .instrument_interface_factory import InstrumentInterfaceFactory


@InstrumentInterfaceFactory.register
class CurrentSource(BaseInstrument):
    """Current source interface with set, get, on & off abstract methods"""

    @abstractmethod
    def on(self) -> None:
        """Start CurrentSource output"""

    @abstractmethod
    def off(self) -> None:
        """Stop CurrentSource outout"""
