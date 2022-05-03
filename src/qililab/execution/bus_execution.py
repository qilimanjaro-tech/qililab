"""BusExecution class."""
from dataclasses import dataclass

from qililab.platform import Bus
from qililab.pulse.pulse_sequence import PulseSequence


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

    @property
    def pulses(self):
        """BusExecution 'pulses' property.

        Returns:
            Tuple[List[float], List[float]]: Dictionary containing a list of the I/Q amplitudes of the pulses applied on this bus.
        """
        return self.pulse_sequence.waveforms

    @property
    def qubit_ids(self):
        """BusExecution 'qubit_id' property

        Returns:
            int: ID of the qubit connected to the bus.
        """
        return self.bus.qubit_ids
