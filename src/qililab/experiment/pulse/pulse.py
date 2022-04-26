"""Pulse class."""
from dataclasses import dataclass


@dataclass
class Pulse:
    """Describes a single pulse to be added to waveform array."""

    @dataclass
    class PulseSettings:
        """Contains the settings of a Pulse.

        Args:
            start (float): Start time of the pulse (ns).
            duration (float): Pulse duration (ns).
            amplitude (float): Pulse digital amplitude (unitless) [0 to 1].
            frequency (float): Pulse intermediate frequency (Hz) [10e6 to 300e6].
            phase (float): Pulse phase.
            shape: (str): Pulse shape.
            offset_i (float): Optional pulse I offset (unitless). amplitude + offset should be in range [0 to 1].
            offset_q (float): Optional pulse Q offset (unitless). amplitude + offset should be in range [0 to 1].
        """

        start: float
        duration: float
        amplitude: float
        frequency: float
        phase: float
        shape: str
        offset_i: float
        offset_q: float

    settings: PulseSettings
