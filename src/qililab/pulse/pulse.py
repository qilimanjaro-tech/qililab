"""Pulse class."""
from dataclasses import InitVar, dataclass, field
from typing import Optional

import numpy as np

from qililab.constants import YAML
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.pulse.pulse_shape.utils.pulse_shape_hashtable import PulseShapeHashTable


@dataclass
class Pulse:
    """Describes a single pulse to be added to waveform array."""

    readout: bool
    start: int
    duration: int
    amplitude: float
    phase: float
    pulse_shape: PulseShape = field(init=False)
    shape: InitVar[dict]
    qubit_id: int
    frequency: Optional[float] = None  # frequency is set by the QRM
    index: int = field(
        init=False
    )  # FIXME: This index is only for Qblox (it points to the specific waveform in the used dictionary), find where to put it

    def __post_init__(self, shape: dict):
        """Cast pulse_shape attribute to its corresponding class."""
        self.pulse_shape = PulseShapeHashTable.get(name=shape[YAML.NAME])(**shape)

    def modulated_waveforms(self, resolution: float = 1.0) -> np.ndarray:
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            NDArray: I and Q modulated waveforms.
        """
        # TODO: Find where to put this method
        if self.frequency is None:
            raise AttributeError("You must define a frequency for the pulse.")

        envelope = self.envelope(resolution=resolution)
        envelopes = [np.real(envelope), np.imag(envelope)]
        time = np.arange(self.duration / resolution) * 1e-9 * resolution
        cosalpha = np.cos(2 * np.pi * self.frequency * time + self.phase)
        sinalpha = np.sin(2 * np.pi * self.frequency * time + self.phase)
        mod_matrix = np.array([[cosalpha, sinalpha], [-sinalpha, cosalpha]])
        return np.transpose(np.einsum("abt,bt->ta", mod_matrix, envelopes))

    def envelope(self, resolution: float = 1.0):
        """Pulse 'envelope' property.

        Returns:
            List[float]: Amplitudes of the envelope of the pulse. Max amplitude is fixed to 1.
        """
        return self.pulse_shape.envelope(duration=self.duration, amplitude=1.0, resolution=resolution)

    def __repr__(self):
        """Return string representation of the Pulse object."""
        return f"""P(s={self.start}, d={self.duration}, a={self.amplitude}, f={self.frequency}, p={self.phase}, {self.pulse_shape.name})"""

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
            and self.frequency == other.frequency
            and self.phase == other.phase
            and self.pulse_shape == other.pulse_shape
        )
