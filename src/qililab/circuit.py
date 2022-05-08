"""HardwareCircuit class"""
from typing import List

from numpy import ndarray
from qibo.core.circuit import Circuit

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.experiment import Experiment
from qililab.gates import HardwareGate


class HardwareCircuit(Circuit):
    """Class used to create circuit model.

    Args:
        nqubits (int): Number of qubits.
    """

    queue: List[HardwareGate]

    def execute(self, initial_state: ndarray = None, nshots: int = None):
        """Executes a pulse sequence"""
        experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME)
        for gate in self.queue:
            experiment.add_gate(gate=gate)
