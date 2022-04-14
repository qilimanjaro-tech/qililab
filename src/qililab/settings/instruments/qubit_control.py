"""Qubit control settings class"""
from dataclasses import dataclass

from qililab.settings.instruments.instrument import InstrumentSettings


@dataclass
class QubitControlSettings(InstrumentSettings):
    """Contains the settings of a specific pulsar.

    Args:
        id (str): ID of the settings.
        name (str): Unique name of the settings.
        category (str): General name of the settings category. Options are "platform", "qubit_control",
        "qubit_readout", "signal_generator", "qubit", "resonator" and "schema".
        ip (str): IP address of the instrument.
    """
