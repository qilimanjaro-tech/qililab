from dataclasses import dataclass

from qililab.circuit.operations.operation import Operation
from qililab.typings.enums import OperationMultiplicity, OperationName


@dataclass
class Measure(Operation):
    """Operation representing a measurement."""

    def __post_init__(self):
        self.name = OperationName.MEASURE
        self.multiplicity = OperationMultiplicity.MULTIPLEXED
        self.parameters = {}
