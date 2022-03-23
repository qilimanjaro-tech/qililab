from numpy import ndarray
from qibo import K
from qibo.config import raise_error
from qibo.core.circuit import Circuit


class HardwareCircuit(Circuit):
    """Class used to create circuit model"""

    def __init__(self, nqubits: int) -> None:
        """
        Args:
            nqubits (int): Number of qubits.
        """
        super().__init__(nqubits)

    def execute(self, initial_state: ndarray = None, nshots: int = None):
        """Executes a pulse sequence"""
        raise_error(NotImplementedError)
