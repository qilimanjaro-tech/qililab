from dataclasses import dataclass, field

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.pulse_operations.pulse_operation import PulseOperation
from qililab.typings.enums import OperationMultiplicity, OperationName
from qililab.utils import classproperty


@OperationFactory.register
@dataclass
class DRAGPulse(PulseOperation):
    """Operation representing a DRAG pulse

    Args:
        amplitude (float): amplitude of the pulse
        duration (int): duration of the pulse in ns
        sigma (float): sigma coefficient
        delta (float): delta coefficient
    """

    amplitude: float
    duration: int
    sigma: float
    delta: float

    def __post_init__(self):
        self.parameters = {
            "amplitude": self.amplitude,
            "duration": self.duration,
            "sigma": self.sigma,
            "delta": self.delta,
        }

    @classproperty
    def name(self) -> OperationName:
        return OperationName.DRAG

    @classproperty
    def multiplicity(self) -> OperationMultiplicity:
        return OperationMultiplicity.PARALLEL
