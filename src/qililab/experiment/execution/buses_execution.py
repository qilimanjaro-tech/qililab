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

    settings: BusesExecutionSettings

    def __init__(self, settings: dict):
        self.settings = self.BusesExecutionSettings(**settings)
