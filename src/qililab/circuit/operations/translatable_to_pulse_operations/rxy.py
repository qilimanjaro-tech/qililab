from dataclasses import dataclass, field

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.translatable_to_pulse_operations.translatable_to_pulse_operation import (
    TranslatableToPulseOperation,
)
from qililab.typings import OperationName
from qililab.typings.enums import Qubits
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

    @classproperty
    def name(self) -> OperationName:
        return OperationName.RXY

    @classproperty
    def num_qubits(self) -> Qubits:
        """Get number of qubits the operation can act upon

        Returns:
            Qubits: The number of qubits the operation can act upon
        """
        return Qubits.ONE

    @property
    def parameters(self):
        """Get the names and values of all parameters as dictionary

        Returns:
            Parameters: The parameters of the operation
        """
        return {"theta": self.theta, "phi": self.phi}


@OperationFactory.register
@dataclass
class R180(Rxy):
    """R180 Operation

    Operation representing a pi rotation around XY axis

    Args:
        phi (float): phi angle in degrees
    """

    theta: float = field(init=False, default=180)
    phi: float

    @classproperty
    def name(self) -> OperationName:
        """Get operation's name

        Returns:
            OperationName: The operation's name
        """
        return OperationName.R180

    @property
    def parameters(self):
        """Get the names and values of all parameters as dictionary

        Returns:
            Parameters: The parameters of the operation
        """
        return {"phi": self.phi}


@OperationFactory.register
@dataclass
class X(R180):
    """X Operation

    Operation representing a pi rotation around XY axis with zero phase. It is the equivelant to an X gate.
    """

    theta: float = field(init=False, default=180)
    phi: float = field(init=False, default=0)

    @classproperty
    def name(self) -> OperationName:
        """Get operation's name

        Returns:
            OperationName: The operation's name
        """
        return OperationName.X

    @property
    def parameters(self):
        """Get the names and values of all parameters as dictionary

        Returns:
            Parameters: The parameters of the operation
        """
        return {}
