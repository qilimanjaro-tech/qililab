from dataclasses import dataclass

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.translatable_to_pulse_operations.translatable_to_pulse_operation import (
    TranslatableToPulseOperation,
)
from qililab.typings.enums import OperationMultiplicity, OperationName
from qililab.utils import classproperty


@OperationFactory.register
@dataclass
class Measure(TranslatableToPulseOperation):
    """Operation representing a measurement."""

    @classproperty
    def name(self) -> OperationName:
        """Get operation's name

        Returns:
            OperationName: The operation's name
        """
        return OperationName.MEASURE

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
