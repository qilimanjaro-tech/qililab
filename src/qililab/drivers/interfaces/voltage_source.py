""" Module containing the interface for the voltage_sources """
from abc import abstractmethod

from qililab.typings.factory_element import FactoryElement

from .base_instrument import BaseInstrument
from .instrument_interface_factory import InstrumentInterfaceFactory


@InstrumentInterfaceFactory.register
class VoltageSource(BaseInstrument, FactoryElement):
    """Voltage source interface with set, get, on & off abstract methods"""

    @abstractmethod
    def on(self) -> None:
        """Start VoltageSource output"""

    @abstractmethod
    def off(self) -> None:
        """Stop VoltageSource outout"""
