"""ExecutionBuilder class"""
from qililab.experiment.execution.buses_execution import BusesExecution
from qililab.experiment.execution.execution import Execution
from qililab.platform import Platform
from qililab.utils import Singleton


class ExecutionBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(self, platform: Platform, buses_execution_settings: BusesExecution.BusesExecutionSettings) -> Execution:
        """Build Execution class.

        Returns:
            Execution: Execution object.
        """
        buses_execution = BusesExecution(settings=buses_execution_settings)

        return Execution(platform=platform, buses=buses_execution)
