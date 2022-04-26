"""Execution class."""
from dataclasses import dataclass
from typing import List

from qililab.experiment.execution.bus_execution import BusExecution
from qililab.platform import Platform


class Execution:
    """Execution class."""

    @dataclass
    class ExecutionSettings:
        """Settings of the execution"""

        buses: List[BusExecution]
        platform: Platform
