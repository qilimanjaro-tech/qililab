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

    @classproperty
    def name(self) -> OperationName:
        """Get operation's name

        Returns:
            OperationName: The operation's name
        """
        return OperationName.GAUSSIAN

    @classproperty
    def multiplicity(self) -> OperationMultiplicity:
        """Get operation's multiplicity

        Returns:
            OperationMultiplicity: The operation's multiplicity
        """
        return OperationMultiplicity.PARALLEL

    @property
    def parameters(self):
        """Get the names and values of all parameters as dictionary

        Returns:
            Parameters: The parameters of the operation
        """
        return {"amplitude": self.amplitude, "duration": self.duration, "sigma": self.sigma}
