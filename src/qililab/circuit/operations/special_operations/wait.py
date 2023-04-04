from dataclasses import dataclass

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.special_operations.special_operation import SpecialOperation
from qililab.typings.enums import OperationMultiplicity, OperationName
from qililab.utils import classproperty


@OperationFactory.register
@dataclass
class Wait(SpecialOperation):
    """Operation representing an idle time of `t` ns.

    Args:
        t (int): Time to wait in ns
    """

    t: int

    @classproperty
    def name(self) -> OperationName:
        """Get operation's name

        Returns:
            OperationName: The operation's name
        """
        return OperationName.WAIT

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
        return {"t": self.t}
