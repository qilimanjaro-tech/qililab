from dataclasses import dataclass

from qililab.circuit.operations.operation import Operation
from qililab.circuit.operations.translatable_to_pulse_operations.translatable_to_pulse_operation import (
    TranslatableToPulseOperation,
)
from qililab.typings.enums import OperationMultiplicity, OperationName


@dataclass
class Measure(TranslatableToPulseOperation):
    """Operation representing a measurement."""

    def __post_init__(self):
        self.name = OperationName.MEASURE
        self.multiplicity = OperationMultiplicity.MULTIPLEXED
        self.parameters = {}
