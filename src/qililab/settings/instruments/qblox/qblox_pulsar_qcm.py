"""Qblox pulsar QCM settings class"""
from dataclasses import dataclass

from qililab.settings.instruments.qubit_control import QubitControlSettings


@dataclass
class QbloxPulsarQCMSettings(QubitControlSettings):
    """Contains the settings of a specific pulsar.

    Args:
        name (str): Name of the settings.
        category (str): Name of the category. Options are "platform", "instrument", "qubit" and "resonator".
        location (str): Path to location of settings file.
        ip (str): IP address of the instrument.
        gain (float): Gain step used by the sequencer.
        reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
        sequencer (int): Index of the sequencer to use.
        sync_enabled (bool): Enable synchronization over multiple instruments.
    """

    reference_clock: str
    sequencer: int
    sync_enabled: bool
