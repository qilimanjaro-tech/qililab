"""Pulse class."""
from dataclasses import dataclass
from typing import ClassVar

from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.pulse.pulse_shape.rectangular import Rectangular
from qililab.typings import PulseName


@dataclass(kw_only=True)
class ReadoutPulse(Pulse):
    """Describes a single pulse to be added to waveform array."""

    name: ClassVar[PulseName] = PulseName.READOUT_PULSE
    pulse_shape: PulseShape = Rectangular()

    def __repr__(self):  # pylint: disable=useless-super-delegation
        """Redirect __repr__ magic method."""
        return super().__repr__()
