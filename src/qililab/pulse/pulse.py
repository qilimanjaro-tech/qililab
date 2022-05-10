"""Pulse class."""
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from qililab.pulse.pulse_shape.pulse_shape import PulseShape


@dataclass
class Pulse:
    """Describes a single pulse to be added to waveform array."""

    name = "Pulse"
    amplitude: float
    phase: float
    duration: int
    qubit_ids: List[int]
    pulse_shape: PulseShape
    start_time: Optional[int] = None

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
        envelope = self.envelope(resolution=resolution)
        envelopes = [np.real(envelope), np.imag(envelope)]
        time = np.arange(self.duration / resolution) * 1e-9 * resolution
        cosalpha = np.cos(2 * np.pi * frequency * time + self.phase)
        sinalpha = np.sin(2 * np.pi * frequency * time + self.phase)
        mod_matrix = np.array([[cosalpha, sinalpha], [-sinalpha, cosalpha]])
        return np.transpose(np.einsum("abt,bt->ta", mod_matrix, envelopes))

    def envelope(self, amplitude: float | None = None, resolution: float = 1.0):
        """Pulse 'envelope' property.

        Returns:
            List[float]: Amplitudes of the envelope of the pulse. Max amplitude is fixed to 1.
        """
        if amplitude is None:
            amplitude = self.amplitude
        return self.pulse_shape.envelope(duration=self.duration, amplitude=amplitude, resolution=resolution)

    @property
    def start(self):
        """Pulse 'start' property.

        Raises:
            ValueError: Is start time is not defined.

        Returns:
            int: Start time of the pulse.
        """
        if self.start_time is None:
            raise ValueError("Start time is not specified.")
        return self.start_time

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
