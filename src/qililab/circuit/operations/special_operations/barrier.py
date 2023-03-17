from dataclasses import dataclass

from qililab.circuit.operations.operation import Operation
from qililab.circuit.operations.special_operations.special_operation import (
    SpecialOperation,
)
from qililab.typings.enums import OperationMultiplicity, OperationName


@dataclass
class Barrier(SpecialOperation):
    """Operation representing a time constraint (forced synchronization)."""

    def __post_init__(self):
        self.name = OperationName.BARRIER
        self.multiplicity = OperationMultiplicity.MULTIPLEXED
        self.parameters = {}
