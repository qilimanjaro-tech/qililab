""" Module containing the interface for the voltage_sources """
from abc import abstractmethod

from .base_instrument import BaseInstrument

class VoltageSource(BaseInstrument):
    """Voltage source interface with set, get, on & off abstract methods"""
    @abstractmethod
    def on(self) -> None:
        """Start VoltageSource output"""

    @abstractmethod
    def off(self) -> None:
        """Stop VoltageSource outout"""
