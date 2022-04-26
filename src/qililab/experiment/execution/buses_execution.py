"""BusesExecution class."""
from dataclasses import dataclass
from typing import List

from qililab.experiment.execution.bus_execution import BusExecution


class BusesExecution:
    """BusesExecution class."""

    @dataclass
    class BusesExecutionSettings:
        """Settings for the BusesExecution class."""

        buses: List[BusExecution]

    settings: BusesExecutionSettings

    def __init__(self, buses_dict: List[dict]):
        buses = [BusExecution(settings) for settings in buses_dict]
        self.settings = self.BusesExecutionSettings(buses)

    def run(self):
        """Run execution."""
        for bus in self.buses:
            bus.run()

    @property
    def buses(self):
        """BusesExecution 'buses' property.

        Returns:
            List[BusExecution]: settings.buses
        """
        return self.settings.buses
