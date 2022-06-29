"""PulseSequence class."""
from dataclasses import dataclass, field
from typing import Dict, List

from qililab.constants import PULSESEQUENCES, YAML
from qililab.pulse.pulse import Pulse
from qililab.pulse.readout_pulse import ReadoutPulse


@dataclass
class PulseSequences:
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
        key = str(pulse.port)
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
            PULSESEQUENCES.PULSES: [pulse.to_dict() for pulse in self.pulses],
            PULSESEQUENCES.TIME: self.time,
            PULSESEQUENCES.DELAY_BETWEEN_PULSES: self.delay_between_pulses,
            PULSESEQUENCES.DELAY_BEFORE_READOUT: self.delay_before_readout,
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Build PulseSequence instance from dictionary.

        Args:
            dictionary (dict): Dictionary description of the class.

        Returns:
            PulseSequence: Class instance.
        """
        delay_between_pulses = dictionary[PULSESEQUENCES.DELAY_BETWEEN_PULSES]
        delay_before_readout = dictionary[PULSESEQUENCES.DELAY_BEFORE_READOUT]
        time = dictionary[PULSESEQUENCES.TIME]
        pulses = [
            Pulse(**settings) if Pulse.name == settings.pop(YAML.NAME) else ReadoutPulse(**settings)
            for settings in dictionary[PULSESEQUENCES.PULSES]
        ]
        return PulseSequences(
            pulses=pulses,
            delay_between_pulses=delay_between_pulses,
            delay_before_readout=delay_before_readout,
            time=time,
        )

    def __iter__(self):
        """Redirect __iter__ magic method to pulses."""
        return self.pulses.__iter__()
