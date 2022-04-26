"""ReadoutPulse class."""
from dataclasses import dataclass

from qililab.experiment.pulse.pulse import Pulse


@dataclass
class ReadoutPulse(Pulse):
    """Describes a readout pulse."""
