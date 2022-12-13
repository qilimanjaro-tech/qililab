""" AWG Qblox Sequencer """


from dataclasses import dataclass

from .awg_sequencer import AWGSequencer


@dataclass
class AWGQbloxSequencer(AWGSequencer):
    """AWG Qblox Sequencer

    Args:
        sync_enabled (bool): Enable synchronization over multiple instruments for this sequencer.
        num_bins (int): Number of bins
    """

    sync_enabled: bool
    num_bins: int
