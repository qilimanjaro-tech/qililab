"""Pulse class."""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import ClassVar

import numpy as np

from qililab.constants import PULSES, RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.utils import Factory, Waveforms
from qililab.utils.signal_processing import modulate


@dataclass(unsafe_hash=True, eq=True)
class Pulse:
    """Describes a single pulse to be added to waveform array."""

    amplitude: float
    phase: float
    duration: int
    frequency: float
    pulse_shape: PulseShape

    def __post_init__(self):
        """Create Pulse Shape"""
        if isinstance(self.pulse_shape, dict):
            self.pulse_shape = Factory.get(name=self.pulse_shape.pop(RUNCARD.NAME))(
                **self.pulse_shape,  # pylint: disable=not-a-mapping
            )

    def modulated_waveforms(
        self, frequency: float = 0.0, resolution: float = 1.0, start_time: float = 0.0
    ) -> Waveforms:
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            frequency (float, optional): The frequency to modulate the pulse in Hz. Defaults to self.frequency.
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.
            start_time (float, optional): The start time of the pulse in ns. Defaults to 0.0.

        Returns:
            Waveforms: I and Q modulated waveforms.
        """
        envelope = self.envelope(resolution=resolution)
        i = np.real(envelope)
        q = np.imag(envelope)
        frequency = frequency or self.frequency
        # Convert pulse relative phase to absolute phase by adding the absolute phase at t=start_time.
        phase_offset = self.phase + 2 * np.pi * frequency * start_time * 1e-9
        imod, qmod = modulate(i=i, q=q, frequency=frequency, phase_offset=phase_offset)
        return Waveforms(i=imod.tolist(), q=qmod.tolist())

    def envelope(self, amplitude: float | None = None, resolution: float = 1.0):
        """Pulse 'envelope' property.

        Returns:
            List[float]: Amplitudes of the envelope of the pulse. Max amplitude is fixed to 1.
        """
        if amplitude is None:
            amplitude = self.amplitude
        return self.pulse_shape.envelope(duration=self.duration, amplitude=amplitude, resolution=resolution)

    @classmethod
    def from_dict(cls, dictionary: dict) -> Pulse:
        """Load Pulse object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Pulse object.

        Returns:
            Pulse: Loaded class.
        """
        return cls(**dictionary)

    def to_dict(self):
        """Return dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse.
        """
        return {
            PULSES.AMPLITUDE: self.amplitude,
            PULSES.FREQUENCY: self.frequency,
            PULSES.PHASE: self.phase,
            PULSES.DURATION: self.duration,
            PULSES.PULSE_SHAPE: self.pulse_shape.to_dict(),
        }

    def label(self) -> str:
        """Return short string representation of the Pulse object."""
        return f"{str(self.pulse_shape)} - {self.duration}ns"
