"""PulseEvent class."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, List
from bisect import insort

from qililab.constants import PULSEEVENT, RUNCARD
from qililab.pulse.pulse import Pulse
from qililab.pulse.readout_pulse import ReadoutPulse
from qililab.typings.enums import PulseName
from qililab.utils.waveforms import Waveforms


@dataclass
class PulseEvent:
    """Object representing a group of pulses starting simultaneously at a certain time."""

    pulses: List[Pulse]
    start_time: int
    pulse_names: ClassVar[PulseName] = PulseName.PULSE

    def __post_init__(self):
        """Checks that all the pulses are of the correct type and sorts them based on their frequency in ascending order."""
        for pulse in self.pulses:
            if pulse.name != self.pulse_names:
                raise ValueError(
                    "All Pulse objects inside a PulseEvent should have the same type (Pulse or ReadoutPulse)."
                )
        self.pulses.sort(key=lambda pulse: pulse.frequency)

    def modulated_waveforms(self, resolution: float = 1.0) -> List[Waveforms]:
        """Applies digital quadrature amplitude modulation (QAM) to the pulses envelope.

        Args:
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.

        Returns:
            List[Waveforms]: I and Q modulated waveforms of all the pulses in the event.
        """
        return [pulse.modulated_waveforms(resolution=resolution, start_time=self.start_time) for pulse in self.pulses]

    @property
    def duration(self):
        return max(pulse.duration for pulse in self.pulses)
    
    @property
    def end_time(self):
        return self.start_time + self.duration
    
    def add_pulse(self, pulse: Pulse):
        if pulse.name != self.pulse_names:
            raise ValueError("All Pulse objects inside a PulseEvent should be of the same type (Pulse or ReadoutPulse).")
        insort(self.pulses, pulse, key=lambda pulse: pulse.frequency)
    
    def merge(self, other: PulseEvent):
        if self.start_time != other.start_time:
            raise ValueError("Can't merge PulseEvents with different start_time.")
        for pulse in other.pulses:
            self.add_pulse(pulse)
        
    def to_dict(self):
        """Return dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse.
        """
        return {PULSEEVENT.PULSES: [pulse.to_dict() for pulse in self.pulses.to_dict()], PULSEEVENT.START_TIME: self.start_time}

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load PulseEvent object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseEvent object.

        Returns:
            PulseEvent: Loaded class.
        """
        pulses_list = dictionary[PULSEEVENT.PULSES]
        pulses = [Pulse.from_dict(pulse_dict) if Pulse.name == PulseName(pulse_dict.pop(RUNCARD.NAME)) else ReadoutPulse.from_dict(pulse_dict) for pulse_dict in pulses_list]
        start_time = dictionary[PULSEEVENT.START_TIME]
        return PulseEvent(pulses=pulses, start_time=start_time)

    def __lt__(self, other: PulseEvent):
        """Returns True if and only if self.start_time is less than other.start_time

        Args:
            other (PulseEvent): PulseEvent to compare.

        Returns:
            bool: Comparison evaluation.
        """
        return self.start_time < other.start_time
