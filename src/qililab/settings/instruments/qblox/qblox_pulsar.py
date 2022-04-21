"""Qblox pulsar settings class."""
from dataclasses import dataclass

from qililab.settings.instruments.instrument import InstrumentSettings
from qililab.typings import ReferenceClock


@dataclass
class QbloxPulsarSettings(InstrumentSettings):
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

    reference_clock: ReferenceClock
    sequencer: int
    sync_enabled: bool
    gain: float

    def __post_init__(self):
        """Cast reference_clock to its corresponding Enum class"""
        super().__post_init__()
        self.reference_clock = ReferenceClock(self.reference_clock)
