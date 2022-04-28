"""ExecutionBuilder class"""
from typing import Dict, List

from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME
from qililab.experiment.execution.bus_execution import BusExecution
from qililab.experiment.execution.buses_execution import BusesExecution
from qililab.experiment.execution.execution import Execution
from qililab.instruments.pulse import PULSE_BUILDER
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
        experiment_settings = SETTINGS_MANAGER.load(
            foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=platform.name, filename=experiment_name
        )

        if YAMLNames.PULSE_SEQUENCE.value not in experiment_settings:
            raise ValueError(f"The loaded dictionary should contain the {YAMLNames.PULSE_SEQUENCE.value} key.")

        if YAMLNames.EXECUTION.value not in experiment_settings:
            raise ValueError(f"The loaded dictionary should contain the {YAMLNames.EXECUTION.value} key.")

        buses = [
            self._build_bus_execution(
                bus=bus, pulse_sequence_settings=experiment_settings[YAMLNames.PULSE_SEQUENCE.value]
            )
            for bus in platform.buses
        ]

        buses_execution = BusesExecution(buses=buses)

        return Execution(
            platform=platform, buses_execution=buses_execution, settings=experiment_settings[YAMLNames.EXECUTION.value]
        )

    def _build_bus_execution(self, bus: Bus, pulse_sequence_settings: List[Dict[str, float | str]]) -> BusExecution:
        """Build BusExecution object.

        Args:
            bus_execution_settings (dict): Dictionary containing the settings of the BusExecution object.

        Returns:
            BusExecution: BusExecution object.
        """
        pulse_sequence = PULSE_BUILDER.build(pulse_sequence_settings=pulse_sequence_settings)
        return BusExecution(bus=bus, pulse_sequence=pulse_sequence)
