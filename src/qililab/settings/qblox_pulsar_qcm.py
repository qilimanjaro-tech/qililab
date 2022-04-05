"""Qblox pulsar QCM settings class"""
from dataclasses import dataclass

from qililab.settings.qblox_pulsar import QbloxPulsarSettings


@dataclass
class QbloxPulsarQCMSettings(QbloxPulsarSettings):
    """Contains the settings of a specific pulsar.

    Args:
        ip (str): IP address of the instrument.
        reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
        sequencer (int): Index of the sequencer to use.
        sync_enabled (bool): Enable synchronization over multiple instruments.
        gain (float): Gain step used by the sequencer.
    """
