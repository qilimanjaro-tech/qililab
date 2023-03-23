from dataclasses import dataclass

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.translatable_to_pulse_operations.translatable_to_pulse_operation import (
    TranslatableToPulseOperation,
)
from qililab.typings.enums import OperationMultiplicity, OperationName


@OperationFactory.register
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
