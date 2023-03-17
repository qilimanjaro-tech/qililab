from dataclasses import dataclass

from qililab.circuit.operations.pulse_operations.pulse_operation import PulseOperation
from qililab.typings.enums import OperationMultiplicity, OperationName


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
        self.name = OperationName.GAUSSIAN
        self.multiplicity = OperationMultiplicity.PARALLEL
        self.parameters = {"amplitude": self.amplitude, "duration": self.duration, "sigma": self.sigma}
