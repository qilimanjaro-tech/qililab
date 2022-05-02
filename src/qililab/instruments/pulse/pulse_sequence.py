"""PulseSequence class."""
from dataclasses import dataclass
from typing import List

from qililab.instruments.pulse.pulse import Pulse
from qililab.typings import PulseCategoryOptions


@dataclass
class PulseSequence:
    """List of pulses."""

    category: PulseCategoryOptions
    pulses: List[Pulse]

    def add(self, pulse: Pulse):
        """Add pulse to sequence.

        Args:
            pulse (Pulse): Pulse object.
        """
        if pulse.category != self.category:
            raise ValueError("A single PulseSequence object cannot contain control and readout pulses.")
        self.pulses.append(pulse)

    @property
    def waveforms(self):
        """PulseSequence 'waveforms' property.

        Returns:
            Dict: Dictionary containing the I, Q waveforms."""

    def __iter__(self):
        """Redirect __iter__ magic method to pulses."""
        return self.pulses.__iter__()
