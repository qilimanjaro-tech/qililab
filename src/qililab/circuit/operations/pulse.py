from dataclasses import dataclass, field

from qililab.circuit.operations.operation import Operation
from qililab.typings.enums import OperationMultiplicity


@dataclass
class Pulse(Operation):
    """Operation representing a generic pulse

    Args:
        amplitude (float): amplitude of the pulse
        duration (int): duration of the pulse in ns
    """

    amplitude: float
    duration: int

    def __post_init__(self):
        self._name = "Pulse"
        self._multiplicity = OperationMultiplicity.PARALLEL
        self._parameters = {"amplitude": self.amplitude, "duration": self.duration}


@dataclass
class GaussianPulse(Pulse):
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
        self._name = "Gaussian"
        self._multiplicity = OperationMultiplicity.PARALLEL
        self._parameters = {"amplitude": self.amplitude, "duration": self.duration, "sigma": self.sigma}
