"""Pulse class."""
from dataclasses import InitVar, dataclass
from typing import ClassVar

import numpy as np

from qililab.constants import PULSE, RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseName
from qililab.utils import Factory, Waveforms


@dataclass
class Pulse:
    """Describes a single pulse to be added to waveform array."""

    name: ClassVar[PulseName] = PulseName.PULSE
    amplitude: float
    phase: float
    duration: int
    pulse_shape: PulseShape
    frequency: float | None = None

    def __post_init__(self):
        """Create Pulse Shape"""
        if isinstance(self.pulse_shape, dict):
            self.pulse_shape = Factory.get(name=self.pulse_shape.pop(RUNCARD.NAME))(
                **self.pulse_shape,  # pylint: disable=not-a-mapping
            )

    def modulated_waveforms(self, frequency: float, resolution: float = 1.0, start_time: float = 0.0) -> Waveforms:
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.
            start_time (float, optional): The start time of the pulse in ns. Defaults to 0.0.

        Returns:
            Waveforms: I and Q modulated waveforms.
        """
        envelope = self.envelope(resolution=resolution)
        envelopes = [np.real(envelope), np.imag(envelope)]
        time = np.arange(self.duration / resolution) * 1e-9 * resolution + start_time * 1e-9
        cosalpha = np.cos(2 * np.pi * frequency * time + self.phase)
        sinalpha = np.sin(2 * np.pi * frequency * time + self.phase)
        mod_matrix = (1.0 / np.sqrt(2)) * np.array([[cosalpha, -sinalpha], [sinalpha, cosalpha]])
        imod, qmod = np.transpose(np.einsum("abt,bt->ta", mod_matrix, envelopes))
        return Waveforms(i=imod.tolist(), q=qmod.tolist())

    def envelope(self, amplitude: float | None = None, resolution: float = 1.0):
        """Pulse 'envelope' property.

        Returns:
            List[float]: Amplitudes of the envelope of the pulse. Max amplitude is fixed to 1.
        """
        if amplitude is None:
            amplitude = self.amplitude
        return self.pulse_shape.envelope(duration=self.duration, amplitude=amplitude, resolution=resolution)

    def to_dict(self):
        """Return dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse.
        """
        return {
            PULSE.NAME: self.name.value,
            PULSE.AMPLITUDE: self.amplitude,
            PULSE.FREQUENCY: self.frequency,
            PULSE.PHASE: self.phase,
            PULSE.DURATION: self.duration,
            PULSE.PULSE_SHAPE: self.pulse_shape.to_dict(),
        }

    def __repr__(self):
        """Return string representation of the Pulse object."""
        return f"{str(self.pulse_shape)} - {self.duration}ns"

    def __str__(self):
        """Return string representation of the Pulse object."""
        return self.__repr__()
