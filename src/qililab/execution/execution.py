"""Execution class."""
from qililab.execution.buses_execution import BusesExecution
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
        results = self.run()
        self.close()
        return results

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
        return self.buses_execution.run()

    def close(self):
        """Close connection to the instruments."""
        self.buses_execution.close()

    @property
    def hardware_average(self):
        """Execution 'hardware_average' property.

        Returns:
            int: settings.hardware_average.
        """
        return self.settings.hardware_average

    @property
    def software_average(self):
        """Execution 'software_average' property.

        Returns:
            int: settings.software_average.
        """
        return self.settings.software_average

    @property
    def repetition_duration(self):
        """Execution 'repetition_duration' property.

        Returns:
            int: settings.repetition_duration.
        """
        return self.settings.repetition_duration

    @property
    def delay_between_pulses(self):
        """Execution 'delay_between_pulses' property.

        Returns:
            int: settings.delay_between_pulses.
        """
        return self.settings.delay_between_pulses
