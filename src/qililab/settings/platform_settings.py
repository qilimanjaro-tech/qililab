from dataclasses import dataclass
from typing import Dict, List

from qililab.settings.abstract_settings import AbstractSettings


@dataclass
class PlatformSettings(AbstractSettings):
    """Contains the settings of the platform.

    Args:
        n_qubits (int): Number of qubits.
        hw_avg (int): Hardware average. Number of shots used when executing a sequence.
        sw_avg (float): Software average.
    """

    nqubits: int
    hw_avg: int
    sw_avg: int
    repetition_duration: int  # ns
    delay_between_pulses: int  # ns
    delay_before_readout: int  # ns
    drag_coeff: float
    num_sigmas: float
