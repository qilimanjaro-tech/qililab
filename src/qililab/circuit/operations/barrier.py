from dataclasses import dataclass

from qililab.circuit.operations.operation import Operation
from qililab.typings.enums import OperationMultiplicity, OperationName


@dataclass
class Barrier(Operation):
    """Operation representing a time constraint (forced synchronization)."""

    def __post_init__(self):
        self.name = OperationName.BARRIER
        self.multiplicity = OperationMultiplicity.MULTIPLEXED
        self.parameters = {}
