from dataclasses import dataclass

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.special_operations.special_operation import SpecialOperation
from qililab.typings.enums import OperationMultiplicity, OperationName


@OperationFactory.register
@dataclass
class Reset(SpecialOperation):
    """Operation representing a reset to ground state."""

    def __post_init__(self):
        self.name = OperationName.RESET
        self.multiplicity = OperationMultiplicity.MULTIPLEXED
        self.parameters = {}
