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

    def __post_init__(self):
        self.parameters = {"t": self.t}

    @classproperty
    def name(self) -> OperationName:
        return OperationName.WAIT

    @classproperty
    def multiplicity(self) -> OperationMultiplicity:
        return OperationMultiplicity.MULTIPLEXED
