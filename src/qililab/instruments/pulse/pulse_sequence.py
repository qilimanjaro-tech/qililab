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

    def __init__(self, pulses_dict: List[dict]):
        pulses = [Pulse(settings) for settings in pulses_dict]
        self.settings = self.PulseSequenceSettings(pulses=pulses)

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
