"""ReadoutPulse class."""
from dataclasses import dataclass

from qililab.instruments.pulse.pulse import Pulse


@dataclass
class ReadoutPulse(Pulse):
    """Describes a readout pulse."""
