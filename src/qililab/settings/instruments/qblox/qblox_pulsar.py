"""Qblox pulsar settings class."""
from dataclasses import dataclass

from qililab.settings.instruments.instrument import InstrumentSettings
from qililab.typings import ReferenceClock


@dataclass
class QbloxPulsarSettings(InstrumentSettings):
    """Contains the settings of a specific pulsar.

    Args:
        name (str): Name of the settings.
        category (str): Name of the category. Options are "platform", "instrument", "qubit" and "resonator".
        ip (str): IP address of the instrument.
        reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
        sequencer (int): Index of the sequencer to use.
        sync_enabled (bool): Enable synchronization over multiple instruments.
    """

    reference_clock: str | ReferenceClock
    sequencer: int
    sync_enabled: bool

    def __post_init__(self):
        """Cast reference_clock to its corresponding Enum class"""
        super().__post_init__()
        self.reference_clock = ReferenceClock(self.reference_clock)
