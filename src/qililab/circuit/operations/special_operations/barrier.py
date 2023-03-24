from dataclasses import dataclass

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.special_operations.special_operation import SpecialOperation
from qililab.typings.enums import OperationMultiplicity, OperationName
from qililab.utils import classproperty


@OperationFactory.register
@dataclass
class Barrier(SpecialOperation):
    """Operation representing a time constraint (forced synchronization)."""

    def __post_init__(self):
        self.parameters = {}

    @classproperty
    def name(self) -> OperationName:
        return OperationName.BARRIER

    @classproperty
    def multiplicity(self) -> OperationMultiplicity:
        return OperationMultiplicity.MULTIPLEXED
