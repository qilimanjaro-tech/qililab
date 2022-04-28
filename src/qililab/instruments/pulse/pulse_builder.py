"""PulseBuilder class"""
from typing import Dict, List

from qililab.instruments.pulse.pulse import Pulse
from qililab.instruments.pulse.pulse_sequence import PulseSequence
from qililab.utils import Singleton


class PulseBuilder(metaclass=Singleton):
    """Builder of PulseSequence objects."""

    def build(self, pulse_sequence_settings: List[dict]) -> Dict[int, PulseSequence]:
        """Build PulseSequence objects.

        Returns:
            Dict[int, PulseSequence]: Dictionary containing a PulseSequence for each different qubit.
        """
        pulses = [Pulse(settings) for settings in pulse_sequence_settings]
        pulse_sequences: Dict[int, PulseSequence] = {}

        for pulse in pulses:
            if pulse.qubit_id not in pulse_sequences:
                pulse_sequences[pulse.qubit_id] = PulseSequence(pulses=[pulse])
                continue
            pulse_sequences[pulse.qubit_id].add(pulse=pulse)

        return pulse_sequences
