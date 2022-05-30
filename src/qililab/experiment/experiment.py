"""HardwareExperiment class."""
import json
from dataclasses import asdict
from typing import List

import numpy as np
from qibo.core.circuit import Circuit
from qiboconnection.api import API
from tqdm import tqdm

from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import PLATFORM_MANAGER_DB, Platform
from qililab.pulse import CircuitToPulses, PulseSequences
from qililab.result import Results
from qililab.typings import Category
from qililab.utils import Loop, Plot, nested_dataclass


class Experiment:
    """HardwareExperiment class"""

    @nested_dataclass
    class ExperimentSettings:
        """Experiment settings."""

        hardware_average: int = 1024
        software_average: int = 1
        repetition_duration: int = 200000
        translation: CircuitToPulses.CircuitToPulsesSettings = CircuitToPulses.CircuitToPulsesSettings()

        def __str__(self):
            """Returns a string representation of the experiment settings."""
            return json.dumps(asdict(self), indent=4)

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

    def execute(
        self, loops: Loop | List[Loop] | None = None, connection: API | None = None
    ) -> Results | Results.ExecutionResults:
        """Run execution."""
        results: Results | Results.ExecutionResults
        plot = Plot(connection=connection)
        self._start_instruments()
        if loops is None:
            results = self._execute()
        else:
            loops_tmp = [loops] if isinstance(loops, Loop) else loops
            results = self._execute_loop(loops=loops_tmp, plot=plot)
        self.execution.close()
        return results

    def _execute_loop(self, loops: List[Loop], plot: Plot) -> Results:
        """Loop and execute sequence over given Platform parameters.

        Args:
            plot_id (str): Plot ID.

        Returns:
            List[List[Result]]: List containing the results for each loop execution.
        """

        def recursive_loop(depth: int, results: Results, x_value: float = 0) -> Results:
            """Loop over all given parameters.

            Args:
                depth (int): Depth of the recursive loop.
                results (Results): Results class.
                x_value (float): X value.

            Returns:
                Results: Results class.
            """

            if depth < 0:
                result = self._execute()
                results.add(execution_results=result)
                plot.send_points(x_value=x_value, y_value=np.round(result.probabilities()[-1][0][0], 4))
                return results

            loop = loops[depth]

            if depth == 0:
                plot.create_live_plot(title=self.name, x_label=f"{loop.category.value} {loop.id_}: {loop.parameter}", y_label="Amplitude")

            element, _ = self.platform.get_element(category=Category(loop.category), id_=loop.id_)
            for value in tqdm(loop.range):
                element.set_parameter(name=loop.parameter, value=value)
                results = recursive_loop(depth=depth - 1, results=results, x_value=value)
            return results

        return recursive_loop(depth=len(loops) - 1, results=Results(loops=loops))

    def _execute(self) -> Results.ExecutionResults:
        """Execute pulse sequences.

        Args:
            results (Results): Results class.

        Returns:
            Results.ExecutionResults: ExecutionResults class.
        """
        self.execution.setup()
        return self.execution.run(nshots=self.hardware_average, repetition_duration=self.repetition_duration)

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
