"""PulseEvent class."""
from __future__ import annotations

from bisect import insort
from dataclasses import dataclass
from typing import ClassVar, List

from qililab.constants import PULSEEVENT
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.typings.enums import PulseEventName


@dataclass
class ReadoutEvent(PulseEvent):
    """Describes a single pulse with a start time."""

    pulses: List[Pulse]
    event_type: ClassVar[PulseEventName] = PulseEventName.READOUT

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load PulseEvent object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseEvent object.

        Returns:
            PulseEvent: Loaded class.
        """
        pulses_list = dictionary[PULSEEVENT.PULSES]
        pulses = [Pulse.from_dict(pulse_dict) for pulse_dict in pulses_list]
        start_time = dictionary[PULSEEVENT.START_TIME]
        return cls(pulses=pulses, start_time=start_time)
