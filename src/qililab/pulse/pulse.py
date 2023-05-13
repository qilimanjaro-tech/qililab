"""Pulse class."""
from dataclasses import dataclass

from qililab.constants import PULSE, RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.utils import Factory


@dataclass(frozen=True, eq=True)
class Pulse:
    """Describes a single pulse to be added to waveform array."""

    amplitude: float
    phase: float
    duration: int
    frequency: float
    pulse_shape: PulseShape

    def envelope(self, amplitude: float | None = None, resolution: float = 1.0):
        """Pulse 'envelope' property.

        Returns:
            list[float]: Amplitudes of the envelope of the pulse. Max amplitude is fixed to 1.
        """
        if amplitude is None:
            amplitude = self.amplitude
        return self.pulse_shape.envelope(duration=self.duration, amplitude=amplitude, resolution=resolution)

    @classmethod
    def from_dict(cls, dictionary: dict) -> "Pulse":
        """Load Pulse object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Pulse object.

        Returns:
            Pulse: Loaded class.
        """
        local_dictionary = dictionary.copy()
        pulse_shape_dict = local_dictionary[PULSE.PULSE_SHAPE]
        local_dictionary[PULSE.PULSE_SHAPE] = Factory.get(name=pulse_shape_dict[RUNCARD.NAME]).from_dict(
            pulse_shape_dict
        )

        return cls(**local_dictionary)

    def to_dict(self):
        """Return dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse.
        """
        return {
            PULSE.AMPLITUDE: self.amplitude,
            PULSE.FREQUENCY: self.frequency,
            PULSE.PHASE: self.phase,
            PULSE.DURATION: self.duration,
            PULSE.PULSE_SHAPE: self.pulse_shape.to_dict(),
        }

    def label(self) -> str:
        """Return short string representation of the Pulse object."""
        return f"{str(self.pulse_shape)} - {self.duration}ns"
