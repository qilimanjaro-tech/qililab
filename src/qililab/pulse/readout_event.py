"""PulseEvent class."""
from dataclasses import dataclass, field

from qililab.constants import PULSEEVENT
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.readout_pulse import ReadoutPulse


@dataclass
class ReadoutEvent(PulseEvent):
    """Describes a single pulse with a start time."""

    pulse: ReadoutPulse

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load PulseEvent object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseEvent object.

        Returns:
            PulseEvent: Loaded class.
        """
        pulse_settings = dictionary[PULSEEVENT.PULSE]
        pulse = ReadoutPulse(**pulse_settings)
        start_time = dictionary[PULSEEVENT.START_TIME]
        return ReadoutEvent(pulse=pulse, start_time=start_time)
