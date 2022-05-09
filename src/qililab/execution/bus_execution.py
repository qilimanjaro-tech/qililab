"""BusExecution class."""
from dataclasses import dataclass

from qililab.platform import Bus
from qililab.pulse import BusPulses, Pulse


@dataclass
class BusExecution:
    """BusExecution class."""

    bus: Bus
    pulses: BusPulses

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
        return self.bus.run(pulses=self.pulses.pulses)

    def close(self):
        """Close connection to the instruments."""
        self.bus.close()

    def add_pulse(self, pulse: Pulse):
        """Add pulse to BusExecution.

        Args:
            pulse (Pulse): Pulse object.
        """
        self.pulses.add(pulse=pulse)

    def waveforms(self, resolution: float = 1.0):
        """Return pulses applied on this bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Tuple[List[float], List[float]]: Dictionary containing a list of the I/Q amplitudes of the pulses applied on this bus.
        """
        return self.pulses.waveforms(frequency=self.qubit_instrument.frequency, resolution=resolution)

    @property
    def qubit_ids(self):
        """BusExecution 'qubit_ids' property

        Returns:
            int: ID of the qubit connected to the bus.
        """
        return self.bus.qubit_ids

    @property
    def qubit_instrument(self):
        """BusExecution 'qubit_instrument' property.

        Returns:
            QubitInstrument: bus.qubit_instrument
        """
        return self.bus.qubit_instrument
