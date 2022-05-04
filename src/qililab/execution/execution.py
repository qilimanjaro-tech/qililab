"""Execution class."""
from qililab.execution.buses_execution import BusesExecution
from qililab.instruments import QubitInstrument
from qililab.platform import Platform
from qililab.settings import ExperimentSettings


class Execution:
    """Execution class."""

    def __init__(self, platform: Platform, buses_execution: BusesExecution):
        self.platform = platform
        self.buses_execution = buses_execution

    def execute(self, settings: ExperimentSettings):
        """Run execution."""
        self.connect()
        self.setup(settings=settings)
        self.start()
        results = self.run()
        self.close()
        return results

    def connect(self):
        """Connect to the instruments."""
        self.buses_execution.connect()

    def setup(self, settings: ExperimentSettings):
        """Setup instruments with experiment settings."""
        QubitInstrument.general_setup(settings=settings)
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

    def pulses(self, resolution: float = 1.0):
        """Return pulses applied on each qubit.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Dict[int, np.ndarray]: Dictionary containing a list of the I/Q amplitudes of the control and readout
            pulses applied on each qubit.
        """
        return self.buses_execution.pulses(resolution=resolution)
