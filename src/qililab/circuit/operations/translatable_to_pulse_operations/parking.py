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
    """Operation representing the parking of parking operation."""

    @classproperty
    def name(self) -> OperationName:
        """Get operation's name

        Returns:
            OperationName: The operation's name
        """
        return OperationName.PARKING

    @classproperty
    def multiplicity(self) -> OperationMultiplicity:
        """Get operation's multiplicity

        Returns:
            OperationMultiplicity: The operation's multiplicity
        """
        return OperationMultiplicity.MULTIPLEXED

    @property
    def parameters(self):
        """Get the names and values of all parameters as dictionary

        Returns:
            Parameters: The parameters of the operation
        """
        return {}
