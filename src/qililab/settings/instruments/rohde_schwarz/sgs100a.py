"""Qblox pulsar settings class"""
from dataclasses import dataclass

from qililab.settings.instruments.signal_generator import SignalGeneratorSettings


@dataclass
class SGS100ASettings(SignalGeneratorSettings):
    """Contains the settings of a specific pulsar.

    Args:
        name (str): Name of the settings.
        category (str): Name of the category. Options are "platform", "instrument", "qubit" and "resonator".
        location (str): Path to location of settings file.
        ip (str): IP address of the instrument.
        power (float): Power of the instrument. Value range is (-120, 25).
        frequency (float): Frequency of the instrument. Value range is (1e6, 20e9).
    """
