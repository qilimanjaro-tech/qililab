"""Experiment class"""
from qililab import PLATFORM_MANAGER_DB
from qililab.execution import Execution
from qililab.execution.buses_execution import BusesExecution
from qililab.gates import HardwareGate
from qililab.platform import Platform


class Experiment:
    """Experiment class."""

    platform: Platform
    execution: Execution

    def __init__(self, platform_name: str):
        self.platform = PLATFORM_MANAGER_DB.build(platform_name=platform_name)
        self.execution = Execution(platform=self.platform, buses_execution=BusesExecution())

    def add_gate(self, gate: HardwareGate):
        """Add gate to Execution.

        Args:
            gate (HardwareGate): Hardware gate.
        """
        self.execution.add_gate(gate=gate)
