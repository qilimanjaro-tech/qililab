"""BusesExecution class."""
from dataclasses import dataclass
from typing import List

from qililab.experiment.execution.bus_execution import BusExecution


@dataclass
class BusesExecution:
    """BusesExecution class."""

    buses: List[BusExecution]

    def connect(self):
        """Connect to the instruments."""
        for bus in self.buses:
            bus.connect()

    def setup(self):
        """Setup instruments with platform settings."""
        for bus in self.buses:
            bus.setup()

    def start(self):
        """Start/Turn on the instruments."""
        for bus in self.buses:
            bus.start()

    def run(self):
        """Run the given pulse sequence."""
        results = []
        for bus in self.buses:
            result = bus.run()
            if result is not None:
                results.append(result)

        return results

    def close(self):
        """Close connection to the instruments."""
        for bus in self.buses:
            bus.close()
