"""Execution class."""
from qililab.experiment.execution.buses_execution import BusesExecution
from qililab.instruments import QubitInstrument
from qililab.platform import Platform
from qililab.settings import ExecutionSettings


class Execution:
    """Execution class."""

    settings: ExecutionSettings

    def __init__(self, platform: Platform, buses_execution: BusesExecution, settings: dict):
        self.platform = platform
        self.buses_execution = buses_execution
        self.settings = ExecutionSettings(**settings)

    def execute(self):
        """Run execution."""
        self.connect()
        self.setup()
        self.start()
        self.run()
        self.close()

    def connect(self):
        """Connect to the instruments."""
        self.buses_execution.connect()

    def setup(self):
        """Setup instruments with platform settings."""
        QubitInstrument.general_setup(settings=self.settings)
        self.buses_execution.setup()

    def start(self):
        """Start/Turn on the instruments."""
        self.buses_execution.start()

    def run(self):
        """Run the given pulse sequence."""
        self.buses_execution.run()

    def close(self):
        """Close connection to the instruments."""
        self.buses_execution.close()
