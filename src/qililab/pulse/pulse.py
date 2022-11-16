"""Pulse class."""
from __future__ import annotations

from dataclasses import InitVar, dataclass
from typing import ClassVar

import numpy as np

from qililab.constants import PULSE, PULSESHAPE
from qililab.pulse.pulse_shape import Drag, Gaussian, Rectangular
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseName, PulseShapeName
from qililab.utils import Waveforms


@dataclass(unsafe_hash=True, eq=True)
class Pulse:
    """Describes a single pulse to be added to waveform array."""

    name: ClassVar[PulseName] = PulseName.PULSE
    amplitude: float
    phase: float
    duration: int
    pulse_shape: PulseShape
    frequency: float | None = None

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

    @classmethod
    def from_dict(cls, dictionary: dict) -> Pulse:
        """Load Pulse object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Pulse object.

        Returns:
            Pulse: Loaded class.
        """
        pulse_shape_dictionary = dictionary[PULSE.PULSE_SHAPE]
        pulse_shape = cls._build_shape(pulse_shape_dictionary)
        pulse_settings = dictionary.copy()
        pulse_settings[PULSE.PULSE_SHAPE] = pulse_shape
        return cls(**pulse_settings)

    @classmethod
    def _build_shape(cls, pulse_shape_dictionary: dict) -> PulseShape:
        """Generates a PulseShape object from the given pulse_shape_dictionary.

        Args:
            pulse_shape_dictionary (dict): Dictionary representation of the PulseShape object.

        Returns:
            PulseShape: PulseShape object generated from the dictionary.
        """
        name_class_map = {
            PulseShapeName.DRAG.value: Drag,
            PulseShapeName.GAUSSIAN.value: Gaussian,
            PulseShapeName.RECTANGULAR.value: Rectangular,
        }
        PulseShapeClass = name_class_map[pulse_shape_dictionary[PULSESHAPE.NAME]]
        pulse_shape_dictionary_copy = pulse_shape_dictionary.copy()
        del pulse_shape_dictionary_copy[PULSESHAPE.NAME]
        return PulseShapeClass(**pulse_shape_dictionary_copy)

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

    def label(self) -> str:
        """Return short string representation of the Pulse object."""
        return f"{str(self.pulse_shape)} - {self.duration}ns"
