"""BusesExecution class."""
from dataclasses import dataclass
from typing import List

from qililab.experiment.execution.bus_execution import BusExecution


class BusesExecution:
    """BusesExecution class."""

    @dataclass
    class BusesExecutionSettings:
        """Settings for the BusesExecution class."""

        buses: List[BusExecution.BusExecutionSettings]

        def __post_init__(self):
            """Cast settings to the BusExecutionSettings class."""
            self.buses = [BusExecution.BusExecutionSettings(**settings) for settings in self.buses]

    settings: BusesExecutionSettings

    def __init__(self, settings: dict):
        self.settings = self.BusesExecutionSettings(**settings)

    @property
    def buses(self):
        """BusesExecution 'buses' property.

        Returns:
            List[BusExecution.BusExecutionSettings]: settings.buses
        """
        return self.settings.buses
