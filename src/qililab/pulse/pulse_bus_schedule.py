"""PulseBusSchedule class."""
from bisect import insort
from dataclasses import dataclass, field
from typing import List, Set

import numpy as np

from qililab.constants import PULSEBUSSCHEDULE
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.utils import Waveforms


@dataclass
class PulseBusSchedule:
    """Container of Pulse objects addressed to the same bus."""

    port: int  # FIXME: we may have one port being used by more than one bus. Use virtual ports instead
    timeline: List[PulseEvent] = field(default_factory=list)
    _pulses: Set[Pulse] = field(init=False, default_factory=set)

    def __post_init__(self):
        """Sort timeline and add used pulses to the pulses set if timeline is not empty."""
        if self.timeline:
            self.timeline.sort()
            for pulse_event in self.timeline:
                self._pulses.add(pulse_event.pulse)

    def add(self, pulse: Pulse, start_time: int):
        """Add pulse to sequence that will begin at start_time.
        Args:
            pulse (Pulse): Pulse object.
            start_time (int): Start time in nanoseconds.
        """
        self._pulses.add(pulse)
        insort(self.timeline, PulseEvent(pulse, start_time))

    def add_event(self, pulse_event: PulseEvent):
        """Add pulse event to sequence.
        Args:
            pulse_event (PulseEvent): PulseEvent object.
        """
        self._pulses.add(pulse_event.pulse)
        insort(self.timeline, pulse_event)

    @property
    def end(self) -> int:
        """End of the PulseSequence.
        Returns:
            int: End of the PulseSequence."""
        end = 0
        for event in self.timeline:
            pulse_end = event.start_time + event.pulse.duration
            end = max(pulse_end, end)
        return end

    @property
    def start(self) -> int:
        """Start of the PulseSequence.
        Returns:
            int: Start of the PulseSequence."""
        return self.timeline[0].start_time

    @property
    def duration(self) -> int:
        """Duration of the PulseSequence.
        Returns:
            int: Duration of the PulseSequence."""
        return self.end - self.start

    @property
    def unique_pulses_duration(self) -> int:
        """Duration of the unique pulses, one immediately after the other.
        Returns:
            int: Duration of the unique pulses."""
        return sum(pulse.duration for pulse in self._pulses)

    @property
    def pulses(self):
        """Set of Pulse objects used in this PulseSequence.
        Returns:
            str: The set of Pulse objects."""
        return self._pulses

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.timeline.__iter__()

    def waveforms(self, resolution: float = 1.0) -> Waveforms:
        """PulseSequence 'waveforms' property.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Waveforms: Class containing the I, Q waveforms for a specific qubit.
        """
        waveforms = Waveforms()
        time = 0
        for pulse_event in self.timeline:
            wait_time = round((pulse_event.start - time) / resolution)
            if wait_time > 0:
                waveforms.add(imod=np.zeros(shape=wait_time), qmod=np.zeros(shape=wait_time))
            time += pulse_event.start
            pulse_waveforms = pulse_event.modulated_waveforms(resolution=resolution)
            waveforms += pulse_waveforms
            time += pulse_event.duration

        return waveforms

    def to_dict(self):
        """Return dictionary representation of the class.

        Returns:
            dict: Dictionary representation of the class.
        """
        return {
            PULSEBUSSCHEDULE.TIMELINE: [pulse_event.to_dict() for pulse_event in self.timeline],
            PULSEBUSSCHEDULE.PORT: self.port,
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load PulseSequence object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseSequence object.

        Returns:
            PulseSequence: Loaded class.
        """
        timeline = [PulseEvent.from_dict(event) for event in dictionary[PULSEBUSSCHEDULE.TIMELINE]]
        port = dictionary[PULSEBUSSCHEDULE.PORT]
        return PulseBusSchedule(timeline=timeline, port=port)
