"""PulseEvent class."""
from __future__ import annotations

from bisect import insort
from dataclasses import dataclass, field
from typing import ClassVar, List

from qililab.constants import PULSEEVENT, RUNCARD
from qililab.pulse.pulse import Pulse
from qililab.typings import PulseEventName
from qililab.utils.waveforms import Waveforms


@dataclass
class PulseEvent:
    """Object representing a group of pulses starting simultaneously at a certain time."""

    pulses: List[Pulse]
    start_time: int
    event_type: ClassVar[PulseEventName] = PulseEventName.PULSE

    def __post_init__(self):
        """Sort pulses based on their frequency in ascending order."""
        self.pulses.sort(key=lambda pulse: pulse.frequency)

    def modulated_waveforms(self, resolution: float = 1.0) -> Waveforms:
        """Applies digital quadrature amplitude modulation (QAM) to the pulses envelope.

        Args:
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.

        Returns:
            List[Waveforms]: I and Q modulated waveforms of all the pulses in the event.
        """
        waveforms_list = [
            pulse.modulated_waveforms(resolution=resolution, start_time=self.start_time) for pulse in self.pulses
        ]
        return Waveforms.from_composition(waveforms_list=waveforms_list)

    @property
    def duration(self) -> int:
        """Total duration of the PulseEvent.

        Returns:
            int: duration in ns.
        """
        return max(pulse.duration for pulse in self.pulses)

    @property
    def end_time(self) -> int:
        """End time of the PulseEvent.

        Returns:
            int: end time in ns.
        """
        return self.start_time + self.duration

    def add_pulse(self, pulse: Pulse):
        """Adds a `pulse` to the `PulseEvent`

        Args:
            pulse (Pulse): Pulse to add.
        """
        insort(self.pulses, pulse, key=lambda pulse: pulse.frequency)

    def merge(self, pulse_event: PulseEvent):
        """Merges a `pulse_event` to the caller PulseEvent, adding the pulses of the former to the pulses list.

        Args:
            pulse_event (PulseEvent): PulseEvent to merge.

        Raises:
            ValueError: Can't merge PulseEvents with different start_time.
        """
        if self.start_time != pulse_event.start_time:
            raise ValueError("Can't merge PulseEvents with different start_time.")
        for pulse in pulse_event.pulses:
            self.add_pulse(pulse)

    def to_dict(self):
        """Return dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse.
        """
        return {
            PULSEEVENT.PULSES: [pulse.to_dict() for pulse in self.pulses],
            PULSEEVENT.START_TIME: self.start_time,
        }

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

    def __lt__(self, other: PulseEvent):
        """Returns True if and only if self.start_time is less than other.start_time

        Args:
            other (PulseEvent): PulseEvent to compare.

        Returns:
            bool: Comparison evaluation.
        """
        return self.start_time < other.start_time
