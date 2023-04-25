"""PredistortedPulse abstract base class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from qililab.pulse import Pulse


@dataclass(frozen=True, eq=True)
class PredistortedPulse(ABC):
    """Base class for predistorted pulses."""

    pulse: Pulse | PredistortedPulse

    def modulated_waveforms(self, resolution: float = 1.0, start_time: float = 0.0):
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.
            start_time (float, optional): The start time of the pulse in ns. Defaults to 0.0.

        Returns:
            Waveforms: I and Q modulated waveforms.
        """
        return self.pulse.modulated_waveforms(resolution=resolution, start_time=start_time)

    @abstractmethod
    def envelope(self, amplitude: float | None = None, resolution: float = 1.0):
        """Pulse 'envelope' property.

        Returns:
            List[float]: Amplitudes of the envelope of the pulse. Max amplitude is fixed to 1.
        """

    # TODO: Implement from_dict method.
    # @classmethod
    # def from_dict(cls, dictionary: dict) -> Pulse:
    #     """Load Pulse object from dictionary.

    #     Args:
    #         dictionary (dict): Dictionary representation of the Pulse object.

    #     Returns:
    #         Pulse: Loaded class.
    #     """
    #     return cls.pulse.from_dict(dictionary)

    # FIXME: This is a bit of a hack, but it works.
    def initial_duration(self):
        """
        Returns:
            int: duration of the initial pulse.
        """
        if self.pulse is Pulse:
            return self.pulse.duration
        else:
            return self.pulse.initial_duration()

    def to_dict(self):
        """Return dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse.
        """
        return self.pulse.to_dict()

    def label(self) -> str:
        """Return short string representation of the Pulse object."""
        return self.pulse.label()
