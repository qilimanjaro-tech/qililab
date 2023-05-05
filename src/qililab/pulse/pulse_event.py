"""PulseEvent class."""
from dataclasses import dataclass, field

import numpy as np

from qililab.constants import PULSEEVENT, RUNCARD
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_distortion import PulseDistortion
from qililab.utils import Factory, Waveforms


@dataclass
class PulseEvent:
    """Object representing a Pulse starting at a certain time."""

    pulse: Pulse
    start_time: int
    pulse_distortions: list[PulseDistortion] = field(default_factory=list)

    @property
    def duration(self) -> int:
        """Duration of the pulse in ns."""
        return self.pulse.duration

    @property
    def end_time(self) -> int:
        """End time of the pulse in ns."""
        return self.start_time + self.duration

    @property
    def frequency(self) -> float:
        """Frequency of the pulse in Hz."""
        return self.pulse.frequency

    def modulated_waveforms(self, resolution: float = 1.0, frequency: float = 0.0) -> Waveforms:
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.
            frequency (float, optional): The modulation frequency in Hz, if it is 0.0 then the frequency of the pulse is used. Defaults to 0.0.

        Returns:
            Waveforms: I and Q modulated waveforms.
        """
        return self.pulse.modulated_waveforms(resolution=resolution, start_time=self.start_time, frequency=frequency)

    def envelope(self, amplitude: float | None = None, resolution: float = 1.0) -> np.ndarray:
        """Returns the pulse envelope with the corresponding distortions applied.

        Args:
            amplitude (float, optional): Amplitude of the envelope. Defaults to None.
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.

        Returns:
            np.ndarray: Envelope.
        """
        envelope = self.pulse.envelope(amplitude=amplitude, resolution=resolution)

        for distortion in self.pulse_distortions:
            envelope = distortion.apply(envelope)

        return envelope

    def to_dict(self):
        """Return dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse.
        """
        return {
            PULSEEVENT.PULSE: self.pulse.to_dict(),
            PULSEEVENT.START_TIME: self.start_time,
            PULSEEVENT.PULSE_DISTORTIONS: [distortion.to_dict() for distortion in self.pulse_distortions],
        }

    @classmethod
    def from_dict(cls, dictionary: dict) -> "PulseEvent":
        """Load PulseEvent object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseEvent object.

        Returns:
            PulseEvent: Loaded class.
        """
        pulse_settings = dictionary[PULSEEVENT.PULSE]
        dictionary[PULSEEVENT.PULSE] = Pulse.from_dict(pulse_settings)

        pulse_distortions_list: list[PulseDistortion] = []

        if PULSEEVENT.PULSE_DISTORTIONS in dictionary:
            pulse_distortions_list.extend(
                Factory.get(name=pulse_distortion_dict[RUNCARD.NAME]).from_dict(pulse_distortion_dict)
                for pulse_distortion_dict in dictionary[PULSEEVENT.PULSE_DISTORTIONS]
            )

        dictionary[PULSEEVENT.PULSE_DISTORTIONS] = pulse_distortions_list

        return cls(**dictionary)

    def __lt__(self, other: "PulseEvent"):
        """Returns True if and only if self.start_time is less than other.start_time

        Args:
            other (PulseEvent): PulseEvent to compare.

        Returns:
            bool: Comparison evaluation.
        """
        return self.start_time < other.start_time
