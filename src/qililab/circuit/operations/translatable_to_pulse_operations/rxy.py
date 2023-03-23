from dataclasses import dataclass, field

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.translatable_to_pulse_operations.translatable_to_pulse_operation import (
    TranslatableToPulseOperation,
)
from qililab.typings import OperationName
from qililab.typings.enums import OperationMultiplicity


@OperationFactory.register
@dataclass
class Rxy(TranslatableToPulseOperation):
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
        self.parameters = {"theta": self.theta, "phi": self.phi}


@OperationFactory.register
@dataclass
class R180(Rxy):
    """Operation representing a pi rotation around XY axis

    Args:
        phi (float): phi angle in degrees
    """

    theta: float = field(init=False)
    phi: float

    def __post_init__(self):
        self.theta = 180
        self.name = OperationName.R180
        self.multiplicity = OperationMultiplicity.PARALLEL
        self.parameters = {"phi": self.phi}


@OperationFactory.register
@dataclass
class X(R180):
    """Operation representing a pi rotation around XY axis with zero phase.
    It is the equivelant of a X gate.
    """

    theta: float = field(init=False)
    phi: float = field(init=False)

    def __post_init__(self):
        self.theta = 180
        self.phi = 0
        self.name = OperationName.X
        self.multiplicity = OperationMultiplicity.PARALLEL
        self.parameters = {}
