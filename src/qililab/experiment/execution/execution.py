"""Execution class."""
from dataclasses import dataclass

from qililab.experiment.execution.buses_execution import BusesExecution
from qililab.platform import Platform


class Execution:
    """Execution class."""

    @dataclass
    class ExecutionSettings:
        """Settings of the execution"""

        platform: Platform
        buses_execution: BusesExecution

    settings: ExecutionSettings

    def __init__(self, platform: Platform, buses: BusesExecution):
        self.settings = self.ExecutionSettings(platform=platform, buses_execution=buses)

    def run(self):
        """Run execution."""

    @property
    def platform(self):
        """Execution 'platform' property.

        Returns:
            Platform: settings.platform.
        """
        return self.settings.platform

    @property
    def buses(self):
        """Execution 'buses' property.

        Returns:
            BusesExecution: settings.buses.
        """
        return self.settings.buses_execution
