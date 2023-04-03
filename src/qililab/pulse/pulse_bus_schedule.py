"""PulseBusSchedule class."""
from bisect import insort
from dataclasses import dataclass, field
from typing import List, Set

import numpy as np

from qililab.constants import PULSEBUSSCHEDULE
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.typings import PulseEventName
from qililab.utils import Waveforms


@dataclass
class PulseBusSchedule:
    """Container of Pulse objects addressed to the same bus. All pulses should have the same name
    (Pulse or ReadoutPulse)."""

    port: int  # FIXME: we may have one port being used by more than one bus. Use virtual ports instead
    timeline: List[PulseEvent] = field(default_factory=list)
    _pulses: Set[Pulse] = field(init=False, default_factory=set)

    def __post_init__(self):
        """Sort timeline and add used pulses to the pulses set if timeline is not empty."""
        if not self.timeline:
            return
        self._check_pulse_names()
        self.timeline.sort()
        self._generate_pulses_set()

    def _check_pulse_names(self):
        """Sort timeline and add used pulses to the pulses set."""
        bus_type = self.timeline[0].event_type
        for event in self.timeline:
            if event.event_type != bus_type:
                raise ValueError(
                    "All PulseEvent objects inside a PulseBusSchedule should have the same type (PulseEvent or ReadoutEvent)."
                )

    def _generate_pulses_set(self):
        for event in self.timeline:
            for pulse in event.pulses:
                self._pulses.add(pulse)

    def add_event(self, pulse_event: PulseEvent):
        """Add pulse event to sequence.
        Args:
            pulse_event (PulseEvent): PulseEvent object.
        """
        if self._pulses and pulse_event.event_type != self.name:
            raise ValueError(
                "All PulseEvent objects inside a PulseBusSchedule should have the same type (PulseEvent or ReadoutEvent)."
            )
        for pulse in pulse_event.pulses:
            self._pulses.add(pulse)
        insort(self.timeline, pulse_event)

    @property
    def end(self) -> int:
        """End of the PulseBusSchedule.
        Returns:
            int: End of the PulseBusSchedule."""
        end = 0
        for event in self.timeline:
            end = max(event.end_time, end)
        return end

    @property
    def start(self) -> int:
        """Start of the PulseBusSchedule.
        Returns:
            int: Start of the PulseBusSchedule."""
        return self.timeline[0].start_time

    @property
    def duration(self) -> int:
        """Duration of the PulseBusSchedule.
        Returns:
            int: Duration of the PulseBusSchedule."""
        return self.end - self.start

    @property
    def unique_pulses_duration(self) -> int:
        """Duration of the unique pulses, one immediately after the other.
        Returns:
            int: Duration of the unique pulses."""
        return sum(pulse.duration for pulse in self._pulses)

    @property
    def pulses(self):
        """Set of Pulse objects used in this PulseBusSchedule.
        Returns:
            str: The set of Pulse objects."""
        return self._pulses

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.timeline.__iter__()

    def waveforms(self, resolution: float = 1.0) -> Waveforms:
        """PulseBusSchedule 'waveforms' property.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Waveforms: Class containing the I, Q waveforms for a specific qubit.
        """
        waveforms = Waveforms()
        time = 0
        for pulse_event in self.timeline:
            wait_time = round((pulse_event.start_time - time) / resolution)
            if wait_time > 0:
                waveforms.add(imod=np.zeros(shape=wait_time), qmod=np.zeros(shape=wait_time))
            time += pulse_event.start_time
            pulse_waveforms = pulse_event.modulated_waveforms(resolution=resolution)
            waveforms += pulse_waveforms
            time += pulse_event.duration

        return waveforms

    @property
    def name(self) -> PulseEventName | None:
        """Name of the pulses of the pulse sequence.
        Returns:
            PulseName | None: Name of the pulses if the pulse sequence is not empty, None otherwise.
        """
        return self.timeline[0].event_type if len(self.timeline) > 0 else None

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
        """Load PulseBusSchedule object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseBusSchedule object.

        Returns:
            PulseBusSchedule: Loaded class.
        """
        timeline = [PulseEvent.from_dict(event) for event in dictionary[PULSEBUSSCHEDULE.TIMELINE]]
        port = dictionary[PULSEBUSSCHEDULE.PORT]
        return PulseBusSchedule(timeline=timeline, port=port)
