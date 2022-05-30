"""HardwareExperiment class."""
import json
from dataclasses import asdict, dataclass
from typing import List

import numpy as np
from qibo.core.circuit import Circuit
from qiboconnection.api import API
from tqdm import tqdm

from qililab.config import logger
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import PLATFORM_MANAGER_DB, Platform
from qililab.pulse import CircuitToPulses, PulseSequences
from qililab.result import Results
from qililab.typings import Category
from qililab.utils import Plot, nested_dataclass


class Experiment:
    """HardwareExperiment class"""

    @nested_dataclass
    class ExperimentSettings:
        """Experiment settings."""

        hardware_average: int = 4024
        software_average: int = 1
        repetition_duration: int = 20000
        translation: CircuitToPulses.CircuitToPulsesSettings = CircuitToPulses.CircuitToPulsesSettings()

        def __str__(self):
            """Returns a string representation of the experiment settings."""
            return json.dumps(asdict(self), indent=4)

    @dataclass
    class ExperimentLoop:
        """ExperimentLoop class."""

        category: str | Category
        id_: int
        parameter: str
        start: float
        stop: float
        num: int

        def __post_init__(self):
            self.category = Category(self.category)

        @property
        def range(self) -> np.ndarray:
            """ExperimentLoop 'range' property.

            Returns:
                ndarray: Range of values of loop.
            """
            return np.linspace(start=self.start, stop=self.stop, num=self.num)

    platform: Platform
    execution: Execution
    settings: ExperimentSettings
    sequences: List[PulseSequences]

    def __init__(
        self,
        sequences: List[Circuit | PulseSequences] | Circuit | PulseSequences,
        platform_name: str,
        settings: ExperimentSettings = None,
        experiment_name: str = "experiment",
    ):
        if not isinstance(sequences, list):
            sequences = [sequences]
        self.name = experiment_name
        self.settings = self.ExperimentSettings() if settings is None else settings
        self.platform = PLATFORM_MANAGER_DB.build(platform_name=platform_name)
        self._build_execution(sequence_list=sequences)

    def execute(self, loops: ExperimentLoop | List[ExperimentLoop] | None = None, connection: API | None = None):
        """Run execution."""
        loops_tmp: List[self.ExperimentLoop] | List[None]  # type: ignore
        if loops is None:
            loops_tmp = [loops]
        else:
            loops_tmp = loops if isinstance(loops, list) else [loops]

        plot = Plot(connection=connection)
        self._start_instruments()
        results = self._execute_loop(loops=loops_tmp, plot=plot)
        self.execution.close()
        return results

    def _execute_loop(
        self,
        loops: List[ExperimentLoop] | List[None],
        plot: Plot,
        results: Results = None,
        x_value=0,
    ):
        """Loop and execute sequence over given Platform parameters.

        Args:
            plot_id (str): Plot ID.

        Returns:
            List[List[Result]]: List containing the results for each loop execution.
        """
        if results is None:
            results = Results()
        for loop in loops[:]:
            loops.pop(0)
            if loop is not None:
                plot.create_live_plot(title=self.name, x_label=loop.parameter, y_label="Amplitude")
                element, _ = self.platform.get_element(category=Category(loop.category), id_=loop.id_)
                for value in tqdm(loop.range):
                    logger.info("%s: %f", loop.parameter, value)
                    element.set_parameter(name=loop.parameter, value=value)
                    self._execute_loop(loops=loops, plot=plot, x_value=value, results=results)
            self.execution.setup()
            result = self.execution.run(nshots=self.hardware_average, repetition_duration=self.repetition_duration)
            results.add(execution_results=result)
            # FIXME: In here we only plot the amplitude of the last sequence. Find a way to plot all the
            # sequences in the list
            plot.send_points(x_value=x_value, y_value=np.round(result.probabilities()[-1][0], 4))
        return results

    def set_parameter(self, category: str, id_: int, parameter: str, value: float):
        """Set parameter of a platform element.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
            value (float): New value.
        """
        element, _ = self.platform.get_element(category=Category(category), id_=id_)
        element.set_parameter(name=parameter, value=value)

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
        translator = CircuitToPulses(settings=self.translation)
        self.sequences = []
        for sequence in sequence_list:
            if isinstance(sequence, Circuit):
                sequence = translator.translate(circuit=sequence)
            self.sequences.append(sequence)
        self.execution = EXECUTION_BUILDER.build(platform=self.platform, pulse_sequences=self.sequences)

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
    def repetition_duration(self):
        """Experiment 'repetition_duration' property.

        Returns:
            int: settings.repetition_duration.
        """
        return self.settings.repetition_duration

    @property
    def translation(self):
        """Experiment 'translation' property.

        Returns:
            int: settings.translation.
        """
        return self.settings.translation

    def to_dict(self):
        """Convert Experiment into a dictionary."""
        return {
            "settings": asdict(self.settings),
            "platform_name": self.platform.name,
            "sequence": [sequence.to_dict() for sequence in self.sequences],
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
        return Experiment(sequences=sequences, platform_name=platform_name, settings=settings)

    def __del__(self):
        """Destructor."""
        self.execution.close()
