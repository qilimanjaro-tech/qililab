from dataclasses import dataclass

import numpy as np

from qililab.circuit.operation_factory import OperationFactory
from qililab.circuit.operations.pulse_operations.pulse_operation import PulseOperation
from qililab.typings.enums import OperationName, Qubits
from qililab.utils import classproperty


@OperationFactory.register
@dataclass(unsafe_hash=True)
class DRAGPulse(PulseOperation):
    """Operation representing a DRAG pulse

    Args:
        amplitude (float): amplitude of the pulse
        duration (int): duration of the pulse (ns)
        phase (float): phase of the pulse
        frequency (float): frequency of the pulse (Hz)
        sigma (float): sigma coefficient
        delta (float): delta coefficient
    """

    sigma: float
    delta: float

    @classproperty
    def name(self) -> OperationName:
        """Get operation's name

        Returns:
            OperationName: The operation's name
        """
        return OperationName.DRAG

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
        return super().parameters | {"sigma": self.sigma, "delta": self.delta}

    def envelope(self, amplitude: float | None = None, resolution: float = 1.0):
        """DRAG envelope centered with respect to the pulse.

        Args:
            resolution (float): Resolution of the time steps (ns).

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        amplitude = amplitude or self.amplitude
        sigma = self.duration / self.sigma
        time = np.arange(self.duration / resolution) * resolution
        mu_ = self.duration / 2
        gaussian = amplitude * np.exp(-0.5 * (time - mu_) ** 2 / sigma**2)
        gaussian = (gaussian - gaussian[0]) / (1 - gaussian[0])  # Shift to avoid introducing noise at time 0
        return gaussian + 1j * self.delta * (-(time - mu_) / sigma**2) * gaussian
