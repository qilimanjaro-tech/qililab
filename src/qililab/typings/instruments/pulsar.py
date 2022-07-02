"""Class Pulsar"""
import qblox_instruments

from qililab.typings.instruments.device import Device


class Pulsar(qblox_instruments.Pulsar, Device):
    """Typing class of the Pulsar class defined by Qblox."""

    def module_type(self):
        """return the module type"""
        return super().instrument_type()
