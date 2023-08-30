"""Attenuator Interface."""
from qililab.typings.factory_element import FactoryElement

from .base_instrument import BaseInstrument
from .instrument_interface_factory import InstrumentInterfaceFactory


@InstrumentInterfaceFactory.register
class Attenuator(BaseInstrument, FactoryElement):
    """Interface of an attenuator."""
