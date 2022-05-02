"""BusExecution class."""
from dataclasses import dataclass

from qililab.instruments.pulse.pulse_sequence import PulseSequence
from qililab.platform import Bus


@dataclass
class BusExecution:
    """BusExecution class."""

    bus: Bus
    pulse_sequence: PulseSequence

    def connect(self):
        """Connect to the instruments."""
        self.bus.connect()

    def setup(self):
        """Setup instruments."""
        self.bus.setup()

    def start(self):
        """Start/Turn on the instruments."""
        self.bus.start()

    def run(self):
        """Run the given pulse sequence."""
        return self.bus.run(pulse_sequence=self.pulse_sequence)

    def close(self):
        """Close connection to the instruments."""
        self.bus.close()
