from dataclasses import dataclass

import numpy as np

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.pulse_operations.pulse_operation import PulseOperation
from qililab.typings.enums import OperationName, Qubits
from qililab.utils import classproperty


@OperationFactory.register
@dataclass
class SquarePulse(PulseOperation):
    """Operation representing a DRAG pulse

    Args:
        amplitude (float): amplitude of the pulse
        duration (int): duration of the pulse (ns)
        phase (float): phase of the pulse
        frequency (float): frequency of the pulse (Hz)
    """

    @classproperty
    def name(self) -> OperationName:
        """Get operation's name

        Returns:
            OperationName: The operation's name
        """
        return OperationName.SQUARE

    @classproperty
    def num_qubits(self) -> Qubits:
        """Get number of qubits the operation can act upon

        Returns:
            Qubits: The number of qubits the operation can act upon
        """
        return Qubits.ONE

    def envelope(self, resolution: float = 1.0):
        """Constant amplitude envelope.

        Args:
            resolution (float): Resolution of the time steps (ns).

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        return self.amplitude * np.ones(round(self.duration / resolution))
