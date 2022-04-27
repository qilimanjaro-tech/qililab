"""BusExecution class."""
from dataclasses import dataclass

from qililab.instruments.pulse.pulse_sequence import PulseSequence
from qililab.platform import Bus


@dataclass
class BusExecution:
    """BusExecution class."""

    bus: Bus
    pulse_sequence: PulseSequence

    def run(self):
        """Run execution."""
