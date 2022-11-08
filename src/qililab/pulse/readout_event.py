"""PulseEvent class."""
from dataclasses import dataclass, field

from qililab.constants import PULSEEVENT, RUNCARD
from qililab.pulse import Pulse, ReadoutPulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.typings.enums import PulseName
from qililab.utils.waveforms import Waveforms


@dataclass
class ReadoutEvent(PulseEvent):
    """Describes a single pulse with a start time."""

    pulse: ReadoutPulse
    start_time: int
    end_time: int = field(init=False)
    sort_index = field(init=False)

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
