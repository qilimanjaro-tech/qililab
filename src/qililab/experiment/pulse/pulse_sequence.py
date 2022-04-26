"""PulseSequence class."""
from dataclasses import dataclass, field
from typing import List

from qililab.experiment.pulse.pulse import Pulse


@dataclass
class PulseSequence:
    """List of pulses."""

    @dataclass
    class PulseSequenceSettings:
        """Settings of the PulseSequence class."""

        pulses: List[Pulse.PulseSettings]

    pulses: List[Pulse] = field(default_factory=list)
