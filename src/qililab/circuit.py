from dataclasses import dataclass

from numpy import ndarray


@dataclass
class HardwareCircuit:
    """Class used to create circuit model.

    Args:
        nqubits (int): Number of qubits.
    """

    nqubits: int

    def execute(self, initial_state: ndarray = None, nshots: int = None):
        """Executes a pulse sequence"""
        raise NotImplementedError
