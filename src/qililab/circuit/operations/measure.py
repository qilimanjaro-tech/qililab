from dataclasses import dataclass

from qililab.circuit.operations.operation import Operation
from qililab.typings.enums import OperationMultiplicity


@dataclass
class Measure(Operation):
    """Operation representing a measurement."""

    def __post_init__(self):
        self._name = "Measure"
        self._multiplicity = OperationMultiplicity.MULTIPLEXED
        self._parameters = {}
