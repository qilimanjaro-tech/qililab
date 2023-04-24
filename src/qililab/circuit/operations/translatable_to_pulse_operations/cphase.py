from dataclasses import dataclass

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.translatable_to_pulse_operations.translatable_to_pulse_operation import (
    TranslatableToPulseOperation,
)
from qililab.typings.enums import OperationName, Qubits
from qililab.utils import classproperty


@OperationFactory.register
@dataclass
class CPhase(TranslatableToPulseOperation):
    """Operation representing a controlled phase.

    Args:
        theta (float): theta angle in degrees
    """

    theta: float

    @classproperty
    def name(self) -> OperationName:
        """Get operation's name

        Returns:
            OperationName: The operation's name
        """
        return OperationName.CPHASE

    @classproperty
    def num_qubits(self) -> Qubits:
        """Get number of qubits the operation can act upon

        Returns:
            Qubits: The number of qubits the operation can act upon
        """
        return Qubits.TWO

    @property
    def parameters(self):
        """Get the names and values of all parameters as dictionary

        Returns:
            Parameters: The parameters of the operation
        """
        return {"theta": self.theta}
