from dataclasses import dataclass

from qililab.settings.instrument import InstrumentSettings


@dataclass
class QbloxPulsarSettings(InstrumentSettings):
    """Contains the settings of a specific pulsar.

    Args:
        ip (str): IP address of the instrument.
        reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
        sequencer (int): Index of the sequencer to use.
        sync_enabled (bool): Enable synchronization over multiple instruments.
        gain (float): Gain step used by the sequencer.

    """

    reference_clock: str
    sequencer: int
    sync_enabled: bool
    gain: float
