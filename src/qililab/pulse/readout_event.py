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
