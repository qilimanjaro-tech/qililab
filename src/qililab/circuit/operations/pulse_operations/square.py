from dataclasses import dataclass

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.pulse_operations.pulse_operation import PulseOperation
from qililab.typings.enums import OperationMultiplicity, OperationName
from qililab.utils import classproperty


@OperationFactory.register
@dataclass
class SquarePulse(PulseOperation):
    """Operation representing a DRAG pulse

    Args:
        amplitude (float): amplitude of the pulse
        duration (int): duration of the pulse in ns
        resolution (float): resolution
    """

    amplitude: float
    duration: int
    resolution: float

    def __post_init__(self):
        self.parameters = {"amplitude": self.amplitude, "duration": self.duration, "resolution": self.resolution}

    @classproperty
    def name(self) -> OperationName:
        return OperationName.SQUARE

    @classproperty
    def multiplicity(self) -> OperationMultiplicity:
        return OperationMultiplicity.PARALLEL
