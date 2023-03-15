from dataclasses import dataclass, field

from qililab.circuit.operations.operation import Operation
from qililab.typings import OperationName
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
        self.name = OperationName.RXY
        self.multiplicity = OperationMultiplicity.PARALLEL
        self.parameters = {"phi": self.phi, "theta": self.theta}


@dataclass
class R180(Rxy):
    theta: float = field(init=False)
    phi: float

    def __post_init__(self):
        self.theta = 180
        self.name = OperationName.R180
        self.multiplicity = OperationMultiplicity.PARALLEL
        self.parameters = {"phi": self.phi}


@dataclass
class X(R180):
    theta: float = field(init=False)
    phi: float = field(init=False)

    def __post_init__(self):
        self.theta = 180
        self.phi = 0
        self.name = OperationName.X
        self.multiplicity = OperationMultiplicity.PARALLEL
        self.parameters = {}
