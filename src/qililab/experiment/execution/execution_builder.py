"""ExecutionBuilder class"""
from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME
from qililab.experiment.execution.buses_execution import BusesExecution
from qililab.experiment.execution.execution import Execution
from qililab.platform import Platform
from qililab.settings import SETTINGS_MANAGER
from qililab.typings import YAMLNames
from qililab.utils import Singleton


class ExecutionBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(self, platform: Platform, experiment_name: str) -> Execution:
        """Build Execution class.

        Returns:
            Execution: Execution object.
        """
        execution_settings = SETTINGS_MANAGER.load(
            foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=platform.name, filename=experiment_name
        )
        if YAMLNames.BUSES.value not in execution_settings:
            raise ValueError(f"Execution settings must contain the {YAMLNames.BUSES.value} key.")

        buses_execution = BusesExecution(buses_dict=execution_settings[YAMLNames.BUSES.value])

        return Execution(platform=platform, buses=buses_execution)
