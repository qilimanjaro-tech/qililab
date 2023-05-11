"""Pulse class."""
from dataclasses import dataclass

import numpy as np

from qililab.constants import PULSE, RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.utils import Factory, Waveforms
from qililab.utils.signal_processing import modulate


@dataclass(frozen=True, eq=True)
class Pulse:
    """Describes a single pulse to be added to waveform array."""

    amplitude: float
    phase: float
    duration: int
    frequency: float
    pulse_shape: PulseShape

    def modulated_waveforms(
        self, resolution: float = 1.0, start_time: float = 0.0, frequency: float = 0.0
    ) -> Waveforms:
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.
            start_time (float, optional): The start time of the pulse in ns. Defaults to 0.0.
            frequency (float, optional): The modulation frequency in Hz, if it is 0.0 then the frequency of the pulse is used. Defaults to 0.0.

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
