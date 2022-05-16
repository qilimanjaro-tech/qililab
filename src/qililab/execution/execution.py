"""Execution class."""
from dataclasses import dataclass

from qililab.execution.buses_execution import BusesExecution
from qililab.gates import HardwareGate


@dataclass
class Execution:
    """Execution class."""

    buses_execution: BusesExecution

    def execute(self):
        """Run execution."""
        self.connect()
        self.setup()
        self.start()
        results = self.run()
        self.close()
        return results

    def connect(self):
        """Connect to the instruments."""
        self.buses_execution.connect()

    def setup(self):
        """Setup instruments with experiment settings."""
        self.buses_execution.setup()

    def start(self):
        """Start/Turn on the instruments."""
        self.buses_execution.start()

    def run(self):
        """Run the given pulse sequence."""
        return self.buses_execution.run()

    def close(self):
        """Close connection to the instruments."""
        self.buses_execution.close()

    def draw(self, resolution: float, num_qubits: int):
        """Save figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.buses_execution.draw(resolution=resolution, num_qubits=num_qubits)

    def add_gate(self, gate: HardwareGate):
        """Add gate to BusesExecution.

        Args:
            gate (HardwareGate): Hardware gate.
        """
        self.buses_execution.add_gate(gate=gate)
