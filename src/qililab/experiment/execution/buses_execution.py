"""BusesExecution class."""
from dataclasses import dataclass
from typing import List

from qililab.experiment.execution.bus_execution import BusExecution


@dataclass
class BusesExecution:
    """BusesExecution class."""

    buses: List[BusExecution]

    def run(self):
        """Run execution."""
        for bus in self.buses:
            bus.run()
