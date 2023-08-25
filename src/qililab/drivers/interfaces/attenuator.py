"""Attenuator Interface."""
from .base_instrument import BaseInstrument
from .instrument_interface_factory import InstrumentInterfaceFactory


@InstrumentInterfaceFactory.register
class Attenuator(BaseInstrument):
    """Interface of an attenuator."""
