"""PulseSequence class."""
from dataclasses import dataclass, field
from typing import Dict, List

from qililab.pulse.pulse import Pulse
from qililab.pulse.readout_pulse import ReadoutPulse


@dataclass
class PulseSequence:
    """Class containing a list of pulses used for control/readout of the qubit.

    Args:
        pulses (List[Pulse]): List of pulses.
    """
    delay_between_pulses: int
    delay_before_readout: int
    pulses: List[Pulse] = field(default_factory=list)
    time: Dict[str, int] = field(default_factory=dict)

    def add(self, pulse: Pulse):
        """Add pulse to sequence.

        Args:
            pulse (Pulse): Pulse object.
        """
        key = str(pulse.qubit_ids)
        if key not in self.time:
            self.time[key] = 0
        if pulse.start_time is None:
            if isinstance(pulse, ReadoutPulse):
                pulse.start_time = self.time[key] + self.delay_before_readout
                self.time[key] += pulse.duration + self.delay_before_readout
            else:
                pulse.start_time = self.time[key]
                self.time[key] += pulse.duration + self.delay_between_pulses
        self.pulses.append(pulse)

    def to_dict(self):
        """Return dictionary representation of the class.

        Returns:
            dict: Dictionary representation of the class.
        """
        return {
            "pulses": [pulse.to_dict() for pulse in self.pulses],
            "time": self.time,
            "delay_between_pulses": self.delay_between_pulses,
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Build PulseSequence instance from dictionary.

        Args:
            dictionary (dict): Dictionary description of the class.

        Returns:
            PulseSequence: Class instance.
        """
        delay_between_pulses = dictionary["delay_between_pulses"]
        time = dictionary["time"]
        pulses = [Pulse(**settings) for settings in dictionary["pulses"]]
        return PulseSequence(pulses=pulses, delay_between_pulses=delay_between_pulses, time=time)

    def __iter__(self):
        """Redirect __iter__ magic method to pulses."""
        return self.pulses.__iter__()
