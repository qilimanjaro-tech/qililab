from dataclasses import dataclass
from typing import List

from qililab.platform.components.qubit import Qubit
from qililab.settings.settings import Settings


@dataclass
class ResonatorSettings(Settings):
    """Contains the settings obtained from calibrating the qubit.

    Args:
        qubits (List[int]): List containing the IDs of the qubits connected to the resonator.
    """

    qubits: List[Qubit]

    def __post_init__(self):
        """Cast list of qubits settings to Qubit objects."""
        self.qubits = [Qubit(qubit_settings) for qubit_settings in self.qubits]
