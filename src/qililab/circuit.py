from numpy import ndarray
from qibo.core.circuit import Circuit


class HardwareCircuit(Circuit):
    """Class used to create circuit model.

    Args:
        nqubits (int): Number of qubits.
    """

    def execute(self, initial_state: ndarray = None, nshots: int = None):
        """Executes a pulse sequence"""
        raise NotImplementedError
