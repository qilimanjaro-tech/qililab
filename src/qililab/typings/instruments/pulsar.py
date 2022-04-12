"""Class Pulsar"""
from qblox_instruments import Pulsar as QbloxPulsar

from qililab.typings.instruments.device import Device


class Pulsar(QbloxPulsar, Device):
    """Typing class of the Pulsar class defined by Qblox."""
