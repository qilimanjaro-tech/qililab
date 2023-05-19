""" AWG Qblox Sequencer """


from dataclasses import dataclass

from .awg_sequencer import AWGSequencer


@dataclass
class AWGQbloxSequencer(AWGSequencer):
    """AWG Qblox Sequencer

    Args:
        num_bins (int): Number of bins
    """

    num_bins: int
