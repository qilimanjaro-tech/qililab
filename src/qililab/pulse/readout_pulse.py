"""Pulse class."""
from dataclasses import dataclass

from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.pulse.pulse_shape.rectangular import Rectangular


@dataclass
class ReadoutPulse(Pulse):
    """Describes a single pulse to be added to waveform array."""

    name = "ReadoutPulse"
    pulse_shape: PulseShape = Rectangular()

    def __repr__(self):  # pylint: disable=useless-super-delegation
        """Redirect __repr__ magic method."""
        return super().__repr__()
