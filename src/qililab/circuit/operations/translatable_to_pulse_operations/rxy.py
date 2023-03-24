from dataclasses import dataclass, field

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.translatable_to_pulse_operations.translatable_to_pulse_operation import (
    TranslatableToPulseOperation,
)
from qililab.typings import OperationName
from qililab.typings.enums import OperationMultiplicity
from qililab.utils import classproperty


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
        self.parameters = {"theta": self.theta, "phi": self.phi}

    @classproperty
    def name(self) -> OperationName:
        return OperationName.RXY

    @classproperty
    def multiplicity(self) -> OperationMultiplicity:
        return OperationMultiplicity.PARALLEL


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
        self.parameters = {"phi": self.phi}

    @classproperty
    def name(self) -> OperationName:
        return OperationName.R180


@OperationFactory.register
@dataclass
class X(R180):
    """Operation representing a pi rotation around XY axis with zero phase.
    It is the equivelant to an X gate.
    """

    theta: float = field(init=False)
    phi: float = field(init=False)

    def __post_init__(self):
        self.theta = 180
        self.phi = 0
        self.parameters = {}

    @classproperty
    def name(self) -> OperationName:
        return OperationName.X
