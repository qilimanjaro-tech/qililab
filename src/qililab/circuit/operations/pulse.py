from dataclasses import dataclass, field

from qililab.circuit.operations.operation import Operation
from qililab.typings.enums import OperationMultiplicity, OperationName


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
        self.name = OperationName.PULSE
        self.multiplicity = OperationMultiplicity.PARALLEL
        self.parameters = {"amplitude": self.amplitude, "duration": self.duration}


@dataclass
class SquarePulse(Pulse):
    """Operation representing a DRAG pulse

    Args:
        amplitude (float): amplitude of the pulse
        duration (int): duration of the pulse in ns
        sigma (float): sigma coefficient
    """

    amplitude: float
    duration: int
    resolution: float

    def __post_init__(self):
        self.name = OperationName.GAUSSIAN
        self.multiplicity = OperationMultiplicity.PARALLEL
        self.parameters = {"amplitude": self.amplitude, "duration": self.duration, "resolution": self.resolution}


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
        self.name = OperationName.GAUSSIAN
        self.multiplicity = OperationMultiplicity.PARALLEL
        self.parameters = {"amplitude": self.amplitude, "duration": self.duration, "sigma": self.sigma}


@dataclass
class DRAGPulse(Pulse):
    """Operation representing a DRAG pulse

    Args:
        amplitude (float): amplitude of the pulse
        duration (int): duration of the pulse in ns
        sigma (float): sigma coefficient
    """

    amplitude: float
    duration: int
    sigma: float
    delta: float

    def __post_init__(self):
        self.name = OperationName.GAUSSIAN
        self.multiplicity = OperationMultiplicity.PARALLEL
        self.parameters = {
            "amplitude": self.amplitude,
            "duration": self.duration,
            "sigma": self.sigma,
            "delta": self.delta,
        }
