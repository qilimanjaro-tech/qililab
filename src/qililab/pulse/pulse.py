"""Pulse class."""
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from qililab.pulse.pulse_shape.pulse_shape import PulseShape


@dataclass
class Pulse:
    """Describes a single pulse to be added to waveform array."""

    name = "Pulse"
    amplitude: float
    phase: float
    qubit_ids: List[int]
    pulse_shape: PulseShape
    start: Optional[int] = None
    duration: Optional[int] = None

    def __post_init__(self):
        """Cast qubit_ids to list."""
        if isinstance(self.qubit_ids, int):
            self.qubit_ids = [self.qubit_ids]

    def modulated_waveforms(self, frequency: float, resolution: float = 1.0) -> np.ndarray:
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            NDArray: I and Q modulated waveforms.
        """
        if self.duration is None:
            raise ValueError("Duration of the pulse is not defined.")
        envelope = self.envelope(resolution=resolution)
        envelopes = [np.real(envelope), np.imag(envelope)]
        time = np.arange(self.duration / resolution) * 1e-9 * resolution
        cosalpha = np.cos(2 * np.pi * frequency * time + self.phase)
        sinalpha = np.sin(2 * np.pi * frequency * time + self.phase)
        mod_matrix = np.array([[cosalpha, sinalpha], [-sinalpha, cosalpha]])
        return np.transpose(np.einsum("abt,bt->ta", mod_matrix, envelopes))

    def envelope(self, resolution: float = 1.0):
        """Pulse 'envelope' property.

        Returns:
            List[float]: Amplitudes of the envelope of the pulse. Max amplitude is fixed to 1.
        """
        if self.duration is None:
            raise ValueError("Duration of the pulse is not defined.")
        return self.pulse_shape.envelope(duration=self.duration, amplitude=1.0, resolution=resolution)

    def __repr__(self):
        """Return string representation of the Pulse object."""
        return f"""P(s={self.start}, d={self.duration}, a={self.amplitude}, p={self.phase}, {self.pulse_shape.name})"""

    def __eq__(self, other: object) -> bool:
        """Compare Pulse with another object.

        Args:
            other (object): Pulse object.
        """
        if not isinstance(other, Pulse):
            raise NotImplementedError
        return (
            self.amplitude == other.amplitude
            and self.duration == other.duration
            and self.phase == other.phase
            and self.pulse_shape == other.pulse_shape
        )
