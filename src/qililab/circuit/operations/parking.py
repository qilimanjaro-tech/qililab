from dataclasses import dataclass

from qililab.circuit.operations.operation import Operation
from qililab.typings.enums import OperationMultiplicity, OperationName


@dataclass
class Parking(Operation):
    """Operation representing the parking of cphase operation."""

    def __post_init__(self):
        self.name = OperationName.PARKING
        self.multiplicity = OperationMultiplicity.MULTIPLEXED
        self.parameters = {}
