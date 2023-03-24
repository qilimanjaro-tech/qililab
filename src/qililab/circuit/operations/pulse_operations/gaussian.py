from dataclasses import dataclass

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.pulse_operations.pulse_operation import PulseOperation
from qililab.typings.enums import OperationMultiplicity, OperationName
from qililab.utils import classproperty


@OperationFactory.register
@dataclass
class GaussianPulse(PulseOperation):
    """Operation representing a Gaussian pulse

    Args:
        amplitude (float): amplitude of the pulse
        duration (int): duration of the pulse in ns
        sigma (float): sigma coefficient
    """

    amplitude: float
    duration: int
    sigma: float

    def __post_init__(self):
        self.parameters = {"amplitude": self.amplitude, "duration": self.duration, "sigma": self.sigma}

    @classproperty
    def name(self) -> OperationName:
        return OperationName.GAUSSIAN

    @classproperty
    def multiplicity(self) -> OperationMultiplicity:
        return OperationMultiplicity.PARALLEL
