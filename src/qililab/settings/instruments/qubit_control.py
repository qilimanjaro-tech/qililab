"""Qubit control settings class"""
from dataclasses import dataclass

from qililab.settings.instruments.instrument import InstrumentSettings


@dataclass
class QubitControlSettings(InstrumentSettings):
    """Contains the settings of a specific pulsar.

    Args:
        name (str): Name of the settings.
        category (str): Name of the category. Options are "platform", "instrument", "qubit" and "resonator".
        ip (str): IP address of the instrument.
        gain (float): Gain step used by the sequencer.
    """

    gain: float
