"""PulseSequence class."""
from dataclasses import dataclass, field
from typing import List

from qililab.constants import PULSES, YAML
from qililab.pulse.pulse import Pulse
from qililab.pulse.readout_pulse import ReadoutPulse


@dataclass
class Pulses:
    """Class containing a list of pulses. It is the pulsed representation of a Qibo circuit.

    Args:
        pulses (List[Pulse]): List of pulse sequences.
    """

    elements: List[Pulse] = field(default_factory=list)

    def add(self, pulse: Pulse | List[Pulse]):
        """Add pulse sequence.

        Args:
            pulse_sequence (PulseSequence): Pulse object.
        """
        if isinstance(pulse, list):
            self.elements.extend(pulse)
            return
        self.elements.append(pulse)

    def to_dict(self):
        """Return dictionary representation of the class.

        Returns:
            dict: Dictionary representation of the class.
        """
        return {PULSES.PULSES: [pulse.to_dict() for pulse in self.elements]}

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Build PulseSequence instance from dictionary.

        Args:
            dictionary (dict): Dictionary description of the class.

        Returns:
            PulseSequence: Class instance.
        """
        pulses = [
            Pulse(**settings) if Pulse.name == settings.pop(YAML.NAME) else ReadoutPulse(**settings)
            for settings in dictionary[PULSES.PULSES]
        ]

        return Pulses(elements=pulses)

    def __iter__(self):
        """Redirect __iter__ magic method to pulses."""
        return self.elements.__iter__()
