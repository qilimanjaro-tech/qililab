from dataclasses import dataclass

from numpy import ndarray
from qibo import K
from qibo.core.circuit import Circuit


@dataclass
class HardwareCircuit(Circuit):
    """Class used to create circuit model.

    Args:
        nqubits (int): Number of qubits.
    """

    def __init__(self, nqubits: int) -> None:
        super().__init__(nqubits)

    def execute(self, initial_state: ndarray = None, nshots: int = None):
        """Executes a pulse sequence"""
        raise NotImplementedError
