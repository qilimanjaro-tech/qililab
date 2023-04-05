"""PulseEvent class."""
from __future__ import annotations

from dataclasses import dataclass, field

from qililab.constants import PULSEEVENT, RUNCARD
from qililab.pulse.pulse import Pulse
from qililab.utils.waveforms import Waveforms


@dataclass
class PulseEvent:
    """Object representing a Pulse starting at a certain time."""

    pulse: Pulse
    start_time: int
    end_time: int = field(init=False, repr=False)
    duration: int = field(init=False, repr=False)

    def __post_init__(self):
        """Set the duration of the PulseEvent from that of the Pulse and calculate end_time."""
        self.duration = self.pulse.duration
        self.end_time = self.start_time + self.duration

    def modulated_waveforms(self, resolution: float = 1.0) -> Waveforms:
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.

        Returns:
            Waveforms: I and Q modulated waveforms.
        """
        return self.pulse.modulated_waveforms(resolution=resolution, start_time=self.start_time)

    @property
    def start(self):
        """Pulse 'start' property.

        Raises:
            ValueError: Is start time is not defined.

        Returns:
            int: Start time of the pulse.
        """
        return self.start_time

    def to_dict(self):
        """Return dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse.
        """
        return {PULSEEVENT.PULSE: self.pulse.to_dict(), PULSEEVENT.START_TIME: self.start_time}

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load PulseEvent object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseEvent object.

        Returns:
            PulseEvent: Loaded class.
        """
        pulse_settings = dictionary[PULSEEVENT.PULSE]
        print(dictionary)
        pulse = Pulse.from_dict(pulse_settings)
        start_time = dictionary[PULSEEVENT.START_TIME]
        return PulseEvent(pulse=pulse, start_time=start_time)

    def __lt__(self, other: PulseEvent):
        """Returns True if and only if self.start_time is less than other.start_time

        Args:
            other (PulseEvent): PulseEvent to compare.

        Returns:
            bool: Comparison evaluation.
        """
        return self.start_time < other.start_time
