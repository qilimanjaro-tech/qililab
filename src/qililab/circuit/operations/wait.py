from dataclasses import dataclass

from qililab.circuit.operations.operation import Operation
from qililab.typings.enums import OperationMultiplicity


@dataclass
class Wait(Operation):
    """Operation representing an idle time of `t` ns.

    Args:
        t (int): Time to wait in ns
    """

    t: int

    def __post_init__(self):
        self._name = "Wait"
        self._multiplicity = OperationMultiplicity.MULTIPLEXED
        self._parameters = {"t": self.t}
