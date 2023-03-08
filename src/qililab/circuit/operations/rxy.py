from dataclasses import dataclass, field

from qililab.circuit.operations.operation import Operation
from qililab.typings.enums import OperationMultiplicity


@dataclass
class Rxy(Operation):
    """Operation representing a rotation around XY axis

    Args:
        theta (float): theta angle in degrees
        phi (float): phi angle in degrees
    """

    theta: float
    phi: float

    def __post_init__(self):
        self._name = "Rxy"
        self._multiplicity = OperationMultiplicity.PARALLEL
        self._parameters = {"phi": self.phi, "theta": self.theta}


@dataclass
class R180(Rxy):
    theta: float = field(init=False)
    phi: float

    def __post_init__(self):
        self.theta = 180
        self._name = "R180"
        self._multiplicity = OperationMultiplicity.PARALLEL
        self._parameters = {"phi": self.phi}


@dataclass
class X(R180):
    theta: float = field(init=False)
    phi: float = field(init=False)

    def __post_init__(self):
        self.theta = 180
        self.phi = 0
        self._name = "X"
        self._multiplicity = OperationMultiplicity.PARALLEL
        self._parameters = {}
