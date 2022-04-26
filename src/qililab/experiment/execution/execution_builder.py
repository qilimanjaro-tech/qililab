"""ExecutionBuilder class"""
from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME
from qililab.experiment.execution.bus_execution import BusExecution
from qililab.experiment.execution.buses_execution import BusesExecution
from qililab.experiment.execution.execution import Execution
from qililab.experiment.pulse import PULSE_BUILDER
from qililab.platform import Bus, Platform
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

        self._check_key_exists(key=YAMLNames.BUSES.value, dictionary=execution_settings)

        buses_execution_list = []
        for bus_execution_settings in execution_settings[YAMLNames.BUSES.value]:
            self._check_key_exists(key=YAMLNames.PULSE_SEQUENCE.value, dictionary=bus_execution_settings)
            self._check_key_exists(key=YAMLNames.BUS.value, dictionary=bus_execution_settings)
            buses_execution_list.append(self._build_bus_execution(bus_execution_settings))

        buses_execution = BusesExecution(buses=buses_execution_list)

        return Execution(platform=platform, buses=buses_execution)

    def _build_bus_execution(self, bus_execution_settings: dict) -> BusExecution:
        """Build BusExecution object.

        Args:
            bus_execution_settings (dict): Dictionary containing the settings of the BusExecution object.

        Returns:
            BusExecution: BusExecution object.
        """
        pulse_sequence = PULSE_BUILDER.build(
            pulse_sequence_settings=bus_execution_settings[YAMLNames.PULSE_SEQUENCE.value]
        )
        bus = Bus(settings=bus_execution_settings[YAMLNames.BUS.value])
        return BusExecution(bus=bus, pulse_sequence=pulse_sequence)

    def _check_key_exists(self, key: str, dictionary: dict):
        """Raise ValueError if key not in dictionary.

        Args:
            key (str): key.
            dictionary (dict): dictionary.
        """
        if key not in dictionary:
            raise ValueError(f"Execution settings must contain the {key} key.")
