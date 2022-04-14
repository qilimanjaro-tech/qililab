"""Qblox pulsar settings class"""
from dataclasses import dataclass

from qililab.settings.instruments.signal_generator import SignalGeneratorSettings


@dataclass
class SGS100ASettings(SignalGeneratorSettings):
    """Contains the settings of a specific pulsar.

    Args:
        id (str): ID of the settings.
        name (str): Unique name of the settings.
        category (str): General name of the settings category. Options are "platform", "qubit_control",
        "qubit_readout", "signal_generator", "qubit", "resonator" and "schema".
        ip (str): IP address of the instrument.
        power (float): Power of the instrument. Value range is (-120, 25).
        frequency (float): Frequency of the instrument. Value range is (1e6, 20e9).
    """
