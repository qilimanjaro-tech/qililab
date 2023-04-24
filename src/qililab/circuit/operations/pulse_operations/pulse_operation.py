from abc import abstractmethod
from dataclasses import dataclass

import numpy as np

from qililab.circuit.operations.operation import Operation
from qililab.utils import Factory, Waveforms
from qililab.utils.signal_processing import modulate


@dataclass
class PulseOperation(Operation):
    """Operation representing a generic pulse

    Args:
        amplitude (float): amplitude of the pulse
        duration (int): duration of the pulse (ns)
        phase (float): phase of the pulse
        frequency (float): frequency of the pulse (Hz)
    """

    amplitude: float
    duration: int
    phase: float
    frequency: float

    @property
    def parameters(self):
        """Get the names and values of all parameters as dictionary

        Returns:
            Parameters: The parameters of the operation
        """
        return {
            "amplitude": self.amplitude,
            "duration": self.duration,
            "phase": self.phase,
            "frequency": self.frequency,
        }

    def modulated_waveforms(
        self, resolution: float = 1.0, start_time: float = 0.0, frequency: float = 0.0
    ) -> Waveforms:
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.
            start_time (float, optional): The start time of the pulse in ns. Defaults to 0.0.

        Returns:
            Waveforms: I and Q modulated waveforms.
        """
        frequency = frequency or self.frequency
        envelope = self.envelope(resolution=resolution)
        i = np.real(envelope)
        q = np.imag(envelope)
        # Convert pulse relative phase to absolute phase by adding the absolute phase at t=start_time.
        phase_offset = self.phase + 2 * np.pi * self.frequency * start_time * 1e-9
        imod, qmod = modulate(i=i, q=q, frequency=self.frequency, phase_offset=phase_offset)
        return Waveforms(i=imod.tolist(), q=qmod.tolist())

    @abstractmethod
    def envelope(self, amplitude: float | None = None, resolution: float = 1.0) -> np.ndarray:
        """Compute the amplitudes of the pulse shape envelope.

        Args:
            resolution (float): Resolution of the time steps (ns).

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
