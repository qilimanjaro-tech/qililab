from dataclasses import dataclass

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.translatable_to_pulse_operations.translatable_to_pulse_operation import (
    TranslatableToPulseOperation,
)
from qililab.typings.enums import OperationMultiplicity, OperationName
from qililab.utils import classproperty


@OperationFactory.register
@dataclass
class Parking(TranslatableToPulseOperation):
    """Operation representing the parking of cphase operation."""

    def __post_init__(self):
        self.parameters = {}

    @classproperty
    def name(self) -> OperationName:
        return OperationName.PARKING

    @classproperty
    def multiplicity(self) -> OperationMultiplicity:
        return OperationMultiplicity.MULTIPLEXED
