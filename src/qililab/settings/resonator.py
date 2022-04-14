from dataclasses import dataclass
from typing import List

from qililab.settings.settings import Settings


@dataclass
class ResonatorSettings(Settings):
    """Contains the settings obtained from calibrating the qubit.

    Args:
        id (str): ID of the settings.
        name (str): Unique name of the settings.
        category (str): General name of the settings category. Options are "platform", "qubit_control",
        "qubit_readout", "signal_generator", "qubit", "resonator" and "schema".
        qubits (List[int]): List containing the IDs of the qubits connected to the resonator.
    """

    qubits: List[int]
