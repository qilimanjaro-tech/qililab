"""HardwareExperiment class."""
from dataclasses import asdict
from typing import List, Tuple

import numpy as np
from qibo.core.circuit import Circuit
from qiboconnection.api import API
from tqdm import tqdm

from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import PLATFORM_MANAGER_DB, Platform
from qililab.pulse import CircuitToPulses, PulseSequences
from qililab.result import Result
from qililab.typings import Category
from qililab.utils import nested_dataclass


class Experiment:
    """HardwareExperiment class"""

    @nested_dataclass
    class ExperimentSettings:
        """Experiment settings."""

        hardware_average: int = 4024
        software_average: int = 1
        loop_duration: int = 20000
        circuit_to_pulse = CircuitToPulses.CircuitToPulsesSettings()

    platform: Platform
    execution: Execution
    settings: ExperimentSettings
    sequences: List[PulseSequences]
    _loop_parameters: List[Tuple[str, int, str, List[float]]]

    def __init__(
        self,
        sequences: List[Circuit | PulseSequences] | Circuit | PulseSequences,
        platform_name: str = DEFAULT_PLATFORM_NAME,
        settings: ExperimentSettings = None,
    ):
        if not isinstance(sequences, list):
            sequences = [sequences]
        self._loop_parameters = []
        self.settings = self.ExperimentSettings() if settings is None else settings
        self.platform = PLATFORM_MANAGER_DB.build(platform_name=platform_name)
        PLATFORM_MANAGER_DB.dump(platform=self.platform)
        self._build_execution(sequence_list=sequences)

    def execute(self, connection: API | None = None):
        """Run execution."""
        self._start_instruments()
        plot_id = self._create_live_plot(connection=connection)
        results = (
            self._execute_loop(connection=connection, plot_id=plot_id)
            if self._loop_parameters
            else [self.execution.run(nshots=self.hardware_average, loop_duration=self.loop_duration)]
        )

        self.execution.close()
        return results

    def _execute_loop(self, connection: API | None, plot_id: str | None):
        """Loop and execute sequence over given Platform parameters.

        Args:
            plot_id (str): Plot ID.

        Returns:
            List[List[Result]]: List containing the results for each loop execution.
        """
        results: List[List[Result]] = []
        for category, id_, parameter, loop_range in self._loop_parameters:
            element, _ = self.platform.get_element(category=Category(category), id_=id_)
            for value in tqdm(loop_range):
                logger.info("%s: %f", parameter, value)
                element.set_parameter(name=parameter, value=value)
                self.execution.setup()
                result = self.execution.run(nshots=self.hardware_average, loop_duration=self.loop_duration)
                results.append(result)
                self._send_plot_points(
                    connection=connection,
                    plot_id=plot_id,
                    x_value=value,
                    y_value=np.round(result[0].probabilities()[0], 4),
                )
        return results

    def _start_instruments(self):
        """Connect, setup and start instruments."""
        self.execution.connect()
        self.execution.setup()
        self.execution.start()

    @property
    def parameters(self):
        """Configurable parameters of the platform.

        Returns:
            str: JSON of the platform.
        """
        return str(self.platform)

    def add_parameter_to_loop(self, category: str, id_: int, parameter: str, start: float, stop: float, num: int):
        """Add parameter to loop over during an experiment.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
        """
        loop_range = list(np.linspace(start, stop, num))
        self._loop_parameters.append((category, id_, parameter, loop_range))

    def draw(self, resolution: float = 1.0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.execution.draw(resolution=resolution)

    def _build_execution(self, sequence_list: List[Circuit | PulseSequences]):
        """Build Execution class.

        Args:
            sequence (Circuit | PulseSequence): Sequence of gates/pulses.
        """
        translator = CircuitToPulses(settings=self.circuit_to_pulse)
        self.sequences = []
        for sequence in sequence_list:
            if isinstance(sequence, Circuit):
                sequence = translator.translate(circuit=sequence)
            self.sequences.append(sequence)
        self.execution = EXECUTION_BUILDER.build(platform=self.platform, pulse_sequences=self.sequences)

    def _create_live_plot(self, connection: API | None):
        """Create live plot."""
        if connection is not None:
            # TODO: Create plot for each different BusReadout
            return connection.create_liveplot(plot_type="LINES")

    def _send_plot_points(self, connection: API | None, plot_id: str | None, x_value: float, y_value: float):
        """Send plot points to live plot viewer.

        Args:
            plot_id (str | None): Plot ID.
            x_value (float): X value.
            y_value (float): Y value.
        """
        if plot_id is not None and connection is not None:
            # TODO: Plot voltages of every BusReadout in the platform
            connection.send_plot_points(plot_id=plot_id, x=x_value, y=y_value)

    @property
    def software_average(self):
        """Experiment 'software_average' property.

        Returns:
            int: settings.software_average.
        """
        return self.settings.software_average

    @property
    def hardware_average(self):
        """Experiment 'hardware_average' property.

        Returns:
            int: settings.hardware_average.
        """
        return self.settings.hardware_average

    @property
    def loop_duration(self):
        """Experiment 'loop_duration' property.

        Returns:
            int: settings.loop_duration.
        """
        return self.settings.loop_duration

    @property
    def circuit_to_pulse(self):
        """Experiment 'circuit_to_pulse' property.

        Returns:
            int: settings.circuit_to_pulse.
        """
        return self.settings.circuit_to_pulse

    def to_dict(self):
        """Convert Experiment into a dictionary."""
        return {
            "settings": asdict(self.settings),
            "platform_name": self.platform.name,
            "sequence": [sequence.to_dict() for sequence in self.sequences],
            "parameters": self._loop_parameters,
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load experiment from dictionary.

        Args:
            dictionary (dict): Dictionary description of an experiment.
        """
        settings = cls.ExperimentSettings(**dictionary["settings"])
        platform_name = dictionary["platform_name"]
        sequences = [PulseSequences.from_dict(settings) for settings in dictionary["sequence"]]
        parameters = dictionary["parameters"]
        experiment = Experiment(sequences=sequences, platform_name=platform_name, settings=settings)
        experiment._loop_parameters = parameters
        return experiment

    def __del__(self):
        """Destructor."""
        self.execution.close()
