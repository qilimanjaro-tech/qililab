"""Class Pulsar"""
import qblox_instruments

from qililab.typings.instruments.device import Device


class Pulsar(qblox_instruments.Pulsar, Device):
    """Typing class of the Pulsar class defined by Qblox."""
