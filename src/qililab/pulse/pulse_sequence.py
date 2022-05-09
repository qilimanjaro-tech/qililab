"""PulseSequence class."""
from dataclasses import dataclass, field
from typing import List

from qililab.pulse.pulse import Pulse


@dataclass
class PulseSequence:
    """Class containing a list of pulses used for control/readout of the qubit.

    Args:
        pulses (List[Pulse]): List of pulses.
    """

    pulses: List[Pulse] = field(default_factory=list)

    def add(self, pulse: Pulse):
        """Add pulse to sequence.

        Args:
            pulse (Pulse): Pulse object.
        """
        pulse.start = 0
        pulse.duration = 50
        self.pulses.append(pulse)

    def __iter__(self):
        """Redirect __iter__ magic method to pulses."""
        return self.pulses.__iter__()
