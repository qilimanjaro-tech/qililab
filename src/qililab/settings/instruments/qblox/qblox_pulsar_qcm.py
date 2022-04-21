"""Qblox pulsar QCM settings class"""
from dataclasses import dataclass

from qililab.settings.instruments.qblox.qblox_pulsar import QbloxPulsarSettings
from qililab.settings.instruments.qubit_control import QubitControlSettings


@dataclass
class QbloxPulsarQCMSettings(QbloxPulsarSettings, QubitControlSettings):
    """Contains the settings of a specific pulsar.

    Args:
        id (str): ID of the settings.
        name (str): Unique name of the settings.
        category (str): General name of the settings category. Options are "platform", "qubit_control",
        "qubit_readout", "signal_generator", "qubit", "resonator", "mixer" and "schema".
        ip (str): IP address of the instrument.
        reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
        sequencer (int): Index of the sequencer to use.
        sync_enabled (bool): Enable synchronization over multiple instruments.
        gain (float): Gain step used by the sequencer.
    """
