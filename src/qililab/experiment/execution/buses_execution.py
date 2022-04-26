"""BusesExecution class."""
from dataclasses import dataclass
from typing import List

from qililab.experiment.execution.bus_execution import BusExecution


@dataclass
class BusesExecution:
    """BusesExecution class."""

    @dataclass
    class BusesExecutionSettings:
        """Settings for the BusesExecution class."""

        buses: List[BusExecution.BusExecutionSettings]

    settings: BusesExecutionSettings
