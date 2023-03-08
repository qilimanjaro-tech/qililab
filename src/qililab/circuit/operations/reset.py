from dataclasses import dataclass

from qililab.circuit.operations.operation import Operation
from qililab.typings.enums import OperationMultiplicity


@dataclass
class Reset(Operation):
    """Operation representing a reset to ground state."""

    def __post_init__(self):
        self._name = "Reset"
        self._multiplicity = OperationMultiplicity.MULTIPLEXED
        self._parameters = {}
