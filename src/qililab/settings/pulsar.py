from dataclasses import dataclass
from typing import Dict, List

from qililab.settings import Settings


@dataclass
class PulsarSettings(Settings):
    """Contains the settings of a specific pulsar.

    Args:
        n_qubits (int): Number of qubits.
        hw_avg (int): Hardware average. Number of shots used when executing a sequence.
        sw_avg (float): Software average.
    """

    ip: str
    reference_clock: str
    sequencer: int
    sync_enabled: bool
    is_cluster: bool
    gain: float
    initial_delay: int  # ns
