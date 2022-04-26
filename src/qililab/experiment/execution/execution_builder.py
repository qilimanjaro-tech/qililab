"""ExecutionBuilder class"""
from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME
from qililab.experiment.execution.buses_execution import BusesExecution
from qililab.experiment.execution.execution import Execution
from qililab.platform import Platform
from qililab.settings import SETTINGS_MANAGER
from qililab.utils import Singleton


class ExecutionBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(self, platform: Platform, experiment_name: str) -> Execution:
        """Build Execution class.

        Returns:
            Execution: Execution object.
        """
        buses_execution_settings = SETTINGS_MANAGER.load(
            foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=platform.name, filename=experiment_name
        )
        buses_execution = BusesExecution(settings=buses_execution_settings)

        return Execution(platform=platform, buses=buses_execution)
