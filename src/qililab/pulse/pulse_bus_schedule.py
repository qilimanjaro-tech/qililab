"""BusPulses class."""
from bisect import insort
from dataclasses import dataclass, field
from typing import List, Set

import numpy as np

from qililab.constants import PULSESEQUENCE, RUNCARD
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.readout_pulse import ReadoutPulse
from qililab.typings import PulseName
from qililab.utils import Waveforms


@dataclass
class PulseBusSchedule:
    """Container of Pulse objects addressed to the same bus. All pulses should have the same name
    (Pulse or ReadoutPulse) and have the same frequency."""

    port: int
    timeline: List[PulseEvent] = []
    _pulses: Set[Pulse] = field(init=False)

    def __post_init__(self):
        """Sort timeline and add used pulses to the pulses set if timeline is not empty."""
        if self.timeline:
            self._sort_and_check()

    def _sort_and_check(self):
        """Sort timeline and add used pulses to the pulses set."""
        self.timeline.sort()
        for pulse_event in self.timeline:
            self._pulses.add(pulse_event.pulse)
        reference_pulse = self.timeline[0].pulse
        for pulse in self._pulses:
            if pulse.frequency != reference_pulse.frequency:
                raise ValueError("All Pulse objects inside a PulseSequence should have the same frequency.")
            if pulse.name != reference_pulse.name:
                raise ValueError(
                    "All Pulse objects inside a PulseSequence should have the same type (Pulse or ReadoutPulse)."
                )

    def add(self, pulse: Pulse, start_time: int):
        """Add pulse to sequence that will begin at start_time.
        Args:
            pulse (Pulse): Pulse object.
            start_time (int): Start time in nanoseconds.
        """
        self._check_pulse_validity(pulse)
        self._pulses.add(pulse)
        insort(self.timeline, PulseEvent(pulse, start_time))

    def add_event(self, pulse_event: PulseEvent):
        """Add pulse event to sequence.
        Args:
            pulse_event (PulseEvent): PulseEvent object.
        """
        self._check_pulse_validity(pulse_event.pulse)
        self._pulses.add(pulse_event.pulse)
        insort(self.timeline, pulse_event)

    def _check_pulse_validity(self, pulse: Pulse):
        if self.pulses:
            if pulse.name != self.timeline[0].pulse.name:
                raise ValueError(
                    "All Pulse objects inside a PulseSequence should have the same type (Pulse or ReadoutPulse)."
                )
            if pulse.frequency != self.timeline[0].pulse.frequency:
                raise ValueError("All Pulse objects inside a PulseSequence should have the same frequency.")

    @property
    def end(self) -> int:
        """End of the PulseSequence.
        Returns:
            int: End of the PulseSequence."""
        end = 0
        for event in self.timeline:
            pulse_end = event.start_time + event.pulse.duration
            end = pulse_end if pulse_end > end else end
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

    def waveforms(self, frequency: float, resolution: float = 1.0) -> Waveforms:
        """PulseSequence 'waveforms' property.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Waveforms: Class containing the I, Q waveforms for a specific qubit.
        """
        waveforms = Waveforms()
        time = 0
        for pulse in self.pulses:
            wait_time = round((pulse.start - time) / resolution)
            if wait_time > 0:
                waveforms.add(imod=np.zeros(shape=wait_time), qmod=np.zeros(shape=wait_time))
            time += pulse.start
            pulse_waveforms = pulse.modulated_waveforms(frequency=frequency, resolution=resolution)
            waveforms += pulse_waveforms
            time += pulse.duration

        return waveforms

    @property
    def name(self) -> PulseName | None:
        """Name of the pulses of the pulse sequence.
        Returns:
            PulseName | None: Name of the pulses if the pulse sequence is not empty, None otherwise.
        """
        return self.timeline[0].pulse.name if len(self.timeline) > 0 else None

    @property
    def frequency(self) -> float | None:
        """Frequency of the pulses of the pulse sequence.
        Returns:
            float | None: Frequency of the pulses if the pulse sequence is not empty, None otherwise.
        """
        return self.timeline[0].pulse.frequency if len(self.timeline) > 0 else None

    @property
    def readout_pulse_duration(self):
        """Duration in ns of the longest readout pulse in the pulse sequence.

        Returns:
            int: Duration in ns of the readout pulse
        """
        max_readout_pulse_duration = max(
            pulse.duration for pulse in self.pulses if pulse.name == PulseName.READOUT_PULSE
        )

        if max_readout_pulse_duration == 0:
            raise ValueError("No ReadoutPulse found.")
        return max_readout_pulse_duration

    def to_dict(self):
        """Return dictionary representation of the class.

        Returns:
            dict: Dictionary representation of the class.
        """
        return {
            PULSESEQUENCE.TIMELINE: [pulse_event.to_dict() for pulse_event in self.timeline],
            PULSESEQUENCE.PORT: self.port,
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load PulseSequence object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseSequence object.

        Returns:
            PulseSequence: Loaded class.
        """
        timeline = [PulseEvent.from_dict(event) for event in dictionary[PULSESEQUENCE.TIMELINE]]
        port = dictionary[PULSESEQUENCE.PORT]
        return PulseBusSchedule(timeline=timeline, port=port)
