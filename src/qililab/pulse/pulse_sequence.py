"""PulseSequence class."""
from dataclasses import dataclass, field
from typing import Dict, List

from qililab.pulse.pulse import Pulse


@dataclass
class PulseSequence:
    """Class containing a list of pulses used for control/readout of the qubit.

    Args:
        pulses (List[Pulse]): List of pulses.
    """

    pulses: List[Pulse] = field(default_factory=list)
    delay_between_pulses: int = 0
    time: Dict[str, int] = field(init=False, default_factory=dict)

    def add(self, pulse: Pulse):
        """Add pulse to sequence.

        Args:
            pulse (Pulse): Pulse object.
        """
        key = str(pulse.qubit_ids)
        if key not in self.time:
            self.time[key] = 0
        if pulse.start_time is None:
            pulse.start_time = self.time[key]
            self.time[key] += pulse.duration + self.delay_between_pulses
        self.pulses.append(pulse)

    def to_dict(self):
        return {"pulses": [pulse.to_dict() from pulse in self.pulses],
        "time": self.time,
        "delay_between_pulses": self.delay_between_pulses}

    def __iter__(self):
        """Redirect __iter__ magic method to pulses."""
        return self.pulses.__iter__()
