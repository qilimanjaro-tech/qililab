"""HardwareExperiment class."""
from dataclasses import asdict, dataclass
from typing import List, Tuple

from qibo.core.circuit import Circuit

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import PLATFORM_MANAGER_DB, Platform
from qililab.pulse import PulseSequence
from qililab.typings import Category


class Experiment:
    """HardwareExperiment class"""

    @dataclass
    class ExperimentSettings:
        """Experiment settings."""

        hardware_average: int = 4096
        software_average: int = 10
        repetition_duration: int = 20000

    platform: Platform
    execution: Execution
    settings: ExperimentSettings
    _parameter_dicts: List[Tuple[Category, int, str, float, float, float]] = []

    def __init__(
        self, sequence: Circuit | PulseSequence, platform_name: str = DEFAULT_PLATFORM_NAME, settings: dict = None
    ):
        self.settings = self.ExperimentSettings() if settings is None else self.ExperimentSettings(**settings)
        self.platform = PLATFORM_MANAGER_DB.build(
            platform_name=platform_name, experiment_settings=asdict(self.settings)
        )
        if isinstance(sequence, PulseSequence):
            self.execution = EXECUTION_BUILDER.build(platform=self.platform, pulse_sequence=sequence)

    def execute(self):
        """Run execution."""
        results = []
        for element, parameter, start, stop, step in self._parameters_to_change:
            for value in range(start, stop, step):
                element.set_parameter(name=parameter, value=value)
                results.append(self.execution.execute())
        return results

    @property
    def parameters(self):
        """Configurable parameters of the platform.

        Returns:
            str: JSON of the platform.
        """
        return str(self.platform)

    @property
    def _parameters_to_change(self):
        """Generator returning the information of the parameters to loop over."""
        for category, id_, parameter, start, stop, step in self._parameter_dicts:
            element, _ = self.platform.get_element(category=category, id_=id_)
            yield element, parameter, start, stop, step

    def add_parameter_to_loop(self, category: str, id_: int, parameter: str, start: float, stop: float, step: float):
        """Add parameter to loop over during an experiment.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
        """
        self._parameter_dicts.append((Category(category), id_, parameter, start, stop, step))

    def draw(self, resolution: float = 1.0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.execution.draw(resolution=resolution)
