"""BusPulses class."""
from dataclasses import dataclass, field
from typing import List

import numpy as np

from qililab.pulse.pulse import Pulse
from qililab.utils import Waveforms


@dataclass
class PulseSequence:
    """Container of Pulse objects addressed to the same bus."""

    qubit_ids: List[int]
    pulses: List[Pulse] = field(default_factory=list)
    _name: str | None = field(init=False, default=None)

    def add(self, pulse: Pulse):
        """Add pulse to sequence.

        Args:
            pulse (Pulse): Pulse object.
        """
        if self._name is None:
            self._name = pulse.name
        if pulse.qubit_ids != self.qubit_ids:
            raise ValueError("All Pulse objects inside a BusPulses class should contain the same qubit_ids.")
        if pulse.name != self.name:
            raise ValueError(
                "All Pulse objects inside a BusPulses class should have the same type (Pulse or ReadoutPulse)."
            )
        self.pulses.append(pulse)

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.pulses.__iter__()

    def waveforms(self, frequency: float, resolution: float = 1.0) -> Waveforms:
        """PulseSequence 'waveforms' property.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Waveforms: Class containing the I, Q waveforms for a specific qubit.
        """
        waveforms = Waveforms()
        time = 0
        for pulse in self.pulses:
            wait_time = round((pulse.start - time) / resolution)
            if wait_time > 0:
                waveforms.add(imod=np.zeros(shape=wait_time), qmod=np.zeros(shape=wait_time))
            time += pulse.start
            pulse_waveforms = pulse.modulated_waveforms(frequency=frequency, resolution=resolution)
            waveforms += pulse_waveforms
            time += pulse.duration

        return waveforms

    @property
    def name(self):
        """Name of the pulses of the pulse sequence.

        Returns:
            str: Name of the pulses. Options are "Pulse" or "ReadoutPulse"""
        return self._name
