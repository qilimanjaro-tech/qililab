from dataclasses import dataclass, field

from qililab.circuit.operations.operation import Operation
from qililab.typings.enums import OperationMultiplicity


@dataclass
class Rxy(Operation):
    """Operation representing a rotation around XY axis

    Args:
        phi (float): phi angle in degrees
        theta (float): theta angle in degrees
    """

    phi: float
    theta: float

    def __post_init__(self):
        self._name = "Rxy"
        self._multiplicity = OperationMultiplicity.PARALLEL
        self._parameters = {"phi": self.phi, "theta": self.theta}


@dataclass
class R180(Rxy):
    phi: float = field(init=False)
    theta: float

    def __post_init__(self):
        self.phi = 180
        self._name = "R180"
        self._multiplicity = OperationMultiplicity.PARALLEL
        self._parameters = {"theta": self.theta}


@dataclass
class X(R180):
    phi: float = field(init=False)
    theta: float = field(init=False)

    def __post_init__(self):
        self.phi = 180
        self.theta = 0
        self._name = "X"
        self._multiplicity = OperationMultiplicity.PARALLEL
        self._parameters = {}
