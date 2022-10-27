"""PulseEvent class."""
from dataclasses import dataclass, field

from qililab.pulse import Pulse


@dataclass
class PulseEvent:
    """Describes a single pulse with a start time."""

    pulse: Pulse
    start_time: int
    end_time: int = field(init = False)
    sort_index = field(init=False)

    def __post_init__(self):
        self.sort_index = self.start_time
        self.end_time = self.start_time + self.pulse.duration
