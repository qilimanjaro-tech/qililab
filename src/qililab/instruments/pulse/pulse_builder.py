"""PulseBuilder class"""
from typing import List

from qililab.instruments.pulse.pulse_sequence import PulseSequence
from qililab.utils import Singleton


class PulseBuilder(metaclass=Singleton):
    """Builder of PulseSequence objects."""

    def build(self, pulse_sequence_settings: List[dict]) -> PulseSequence:
        """Build PulseSequence with its corresponding Pulse objects.

        Returns:
            PulseSequence: PulseSequence object.
        """
        return PulseSequence(pulses_dict=pulse_sequence_settings)
