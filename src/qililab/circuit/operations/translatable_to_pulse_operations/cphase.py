from dataclasses import dataclass

from qililab.circuit.operations.operation import Operation
from qililab.circuit.operations.translatable_to_pulse_operations.translatable_to_pulse_operation import (
    TranslatableToPulseOperation,
)
from qililab.typings.enums import OperationMultiplicity, OperationName


@dataclass
class CPhase(TranslatableToPulseOperation):
    """Operation representing a controlled phase.

    Args:
        theta (float): theta angle in degrees
    """

    theta: float

    def __post_init__(self):
        self.name = OperationName.CPHASE
        self.multiplicity = OperationMultiplicity.CONTROLLED
        self.parameters = {"theta": self.theta}
