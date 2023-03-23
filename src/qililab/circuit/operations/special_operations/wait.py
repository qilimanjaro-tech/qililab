from dataclasses import dataclass

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.special_operations.special_operation import SpecialOperation
from qililab.typings.enums import OperationMultiplicity, OperationName


@OperationFactory.register
@dataclass
class Wait(SpecialOperation):
    """Operation representing an idle time of `t` ns.

    Args:
        t (int): Time to wait in ns
    """

    t: int

    def __post_init__(self):
        self.name = OperationName.WAIT
        self.multiplicity = OperationMultiplicity.MULTIPLEXED
        self.parameters = {"t": self.t}
