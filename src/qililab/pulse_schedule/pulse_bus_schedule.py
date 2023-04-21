"""PulseBusSchedule class."""
from __future__ import annotations

from bisect import insort
from dataclasses import dataclass, field
from typing import List, Set

import numpy as np

from qililab.circuit.operations.pulse_operations.pulse_operation import PulseOperation
from qililab.pulse_schedule.pulse_event import PulseEvent
from qililab.utils import Waveforms


@dataclass
class PulseBusSchedule:
    """Container of Pulse objects addressed to the same bus."""

    port: int  # FIXME: we may have one port being used by more than one bus. Use virtual ports instead
    timeline: List[PulseEvent] = field(default_factory=list)
    _pulses: Set[PulseOperation] = field(init=False, default_factory=set)

    def __post_init__(self):
        """Sort timeline and add used pulses to the pulses set if timeline is not empty."""
        if self.timeline:
            self.timeline.sort()
            for pulse_event in self.timeline:
                self._pulses.add(pulse_event.pulse)

    def add_event(self, pulse_event: PulseEvent):
        """Add pulse event to sequence.
        Args:
            pulse_event (PulseEvent): PulseEvent object.
        """
        self._pulses.add(pulse_event.pulse)
        insort(self.timeline, pulse_event)

    def frequencies(self) -> List[float]:
        """Frequencies of the pulses in the sequence.

        Returns:
            List[float]: List of the frequencies in ascending order.
        """
        frequencies_set = {pulse.frequency for pulse in self._pulses}
        return sorted(frequencies_set)

    @property
    def end_time(self) -> int:
        """End of the PulseBusSchedule.
        Returns:
            int: End of the PulseBusSchedule."""
        end = 0
        for event in self.timeline:
            pulse_end = event.start_time + event.pulse.duration
            end = max(pulse_end, end)
        return end

    @property
    def start_time(self) -> int:
        """Start of the PulseBusSchedule.
        Returns:
            int: Start of the PulseBusSchedule."""
        return self.timeline[0].start_time

    @property
    def duration(self) -> int:
        """Duration of the PulseBusSchedule.
        Returns:
            int: Duration of the PulseBusSchedule."""
        return self.end_time - self.start_time

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
            time += wait_time
            pulse_waveforms = pulse_event.modulated_waveforms(resolution=resolution)
            waveforms += pulse_waveforms
            time += pulse_event.duration

        return waveforms

    def with_frequency(self, frequency: float) -> PulseBusSchedule:
        """Filter PulseBusSchedule by frequency.

        Args:
            frequency (float): Frequency to filter the PulseBusSchedule.

        Returns:
            PulseBusSchedule: Filtered PulseBusSchedule.
        """
        filtered_timeline = [pulse_event for pulse_event in self.timeline if pulse_event.frequency == frequency]
        return PulseBusSchedule(port=self.port, timeline=filtered_timeline)
