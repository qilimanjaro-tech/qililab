"""PulseSequence class."""
from dataclasses import dataclass
from typing import List

from qililab.instruments.pulse.pulse import Pulse


class PulseSequence:
    """List of pulses."""

    @dataclass
    class PulseSequenceSettings:
        """Settings of the PulseSequence class."""

        pulses: List[Pulse]

    settings: PulseSequenceSettings

    def __init__(self, pulses: List[Pulse]):
        self.settings = self.PulseSequenceSettings(pulses=pulses)

    def add(self, pulse: Pulse):
        """Add pulse to sequence.

        Args:
            pulse (Pulse): Pulse object.
        """
        self.pulses.append(pulse)

    @property
    def pulses(self):
        """PulseSequence 'pulses' property.

        Returns:
            List[Pulse]: settings.pulses.
        """
        return self.settings.pulses

    @property
    def waveforms(self):
        """PulseSequence 'waveforms' property.

        Returns:
            Dict: Dictionary containing the I, Q waveforms."""

    def __iter__(self):
        """Redirect __iter__ magic method to pulses."""
        return self.pulses.__iter__()
