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
        buses: BusesExecution

    settings: ExecutionSettings

    def __init__(self, platform: Platform, buses: BusesExecution):
        self.settings = self.ExecutionSettings(platform=platform, buses=buses)
