""" AWG Sequencer """


from dataclasses import dataclass

from qililab.instruments.awg_settings.awg_sequencer_path import AWGSequencerPath


@dataclass
class AWGSequencer:
    """AWG Sequencer

    Args:
        identifier (int): The identifier of the sequencer
        path0 (AWGOutputChannel): AWG output channel associated with the path 0 sequencer
        path1 (AWGOutputChannel): AWG output channel associated with the path 1 sequencer
        intermediate_frequency (float): Frequency for each sequencer
        gain (float): Gain step used by the sequencer.
        gain_imbalance (float): Amplitude added to the Q channel.
        phase_imbalance (float): Dephasing.
        hardware_modulation  (bool): Flag to determine if the modulation is performed by the device
        offset_path0 (float): Path0 or I offset (unitless). amplitude + offset should be in range [0 to 1].
        offset_path1 (float): Path1 or Q offset (unitless). amplitude + offset should be in range [0 to 1].
    """

    identifier: int
    path0: AWGSequencerPath
    path1: AWGSequencerPath
    intermediate_frequency: float
    gain: float
    gain_imbalance: float
    phase_imbalance: float
    hardware_modulation: bool
    offset_path0: float
    offset_path1: float
