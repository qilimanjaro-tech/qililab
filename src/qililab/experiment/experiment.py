"""HardwareExperiment class."""
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import numpy as np
from qibo.core.circuit import Circuit
from qiboconnection.api import API
from tqdm.auto import tqdm

from qililab.constants import (
    DATA,
    DATA_FOLDERNAME,
    DEFAULT_PLATFORM_NAME,
    EXPERIMENT_FILENAME,
    LOOP,
    RESULTS_FILENAME,
    YAML,
)
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import PLATFORM_MANAGER_YAML, Platform, RuncardSchema
from qililab.pulse import CircuitToPulses, PulseSequences
from qililab.result import Result, Results
from qililab.typings import Category, Parameter, yaml
from qililab.utils import LivePlot, Loop, nested_dataclass


class Experiment:
    """HardwareExperiment class"""

    @nested_dataclass
    class ExperimentSettings:
        """Experiment settings."""

        hardware_average: int = 1024
        software_average: int = 1
        repetition_duration: int = 200000

        def __str__(self):
            """Returns a string representation of the experiment settings."""
            return yaml.dump(asdict(self), sort_keys=False)

    platform: Platform
    execution: Execution
    settings: ExperimentSettings
    _initial_sequences: List[Circuit | PulseSequences]
    sequences: List[PulseSequences]
    loop: Loop | None

    def __init__(
        self,
        sequences: List[Circuit | PulseSequences] | Circuit | PulseSequences,
        platform_name: str = DEFAULT_PLATFORM_NAME,
        loop: Loop | None = None,
        settings: ExperimentSettings = None,
        experiment_name: str = "experiment",
    ):
        if not isinstance(sequences, list):
            sequences = [sequences]
        self._initial_sequences = sequences
        self.name = experiment_name
        self.settings = self.ExperimentSettings() if settings is None else settings
        self.platform = PLATFORM_MANAGER_YAML.build(platform_name=platform_name)
        self.loop = loop
        self.execution, self.sequences = self._build_execution(sequence_list=self._initial_sequences)

    def execute(self, connection: API | None = None) -> Results:
        """Run execution."""
        path = self._create_folder()
        self._create_results_file(path=path)
        self._dump_experiment_data(path=path)
        plot = LivePlot(connection=connection)
        with self.execution:
            results = self._execute_loop(plot=plot, path=path)
        return results

    def _execute_loop(self, plot: LivePlot, path: Path) -> Results:
        """Loop and execute sequence over given Platform parameters.

        Args:
            plot (LivePlot): LivePlot class used for live plotting.
            path (Path): Path where the data is stored.

        Returns:
            List[List[Result]]: List containing the results for each loop execution.
        """

        if self.loop is None:
            return Results(
                software_average=self.software_average,
                num_sequences=self.execution.num_sequences,
                results=self._execute(plot=plot, path=path),  # type: ignore
            )
        return self.recursive_loop(
            loop=self.loop,
            results=Results(
                software_average=self.software_average,
                shape=self.loop.shape,
                num_sequences=self.execution.num_sequences,
            ),
            path=path,
            plot=plot,
        )

    def recursive_loop(
        self, loop: Loop | None, results: Results, path: Path, plot: LivePlot, x_value: float = 0, depth: int = 0
    ) -> Results:
        """Loop over all the range values defined in the Loop class and change the parameters of the chosen instruments.

        Args:
            loop (Loop | None): Loop class containing the the info of a Platform element and one of its parameters and
            the parameter values to loop over.
            results (Results): Results class containing all the execution results.
            path (Path): Path where the data is stored.
            plot (LivePlot): LivePlot class used for live plotting.
            x_value (float): X value used in live plotting. Defaults to 0.
            depth (int): Depth of the recursive loop. Defaults to 0.

        Returns:
            Results: _description_
        """
        if loop is None:
            return self._execute_and_process_results(results=results, path=path, plot=plot, x_value=x_value)

        if loop.loop is None:
            x_label = self._set_x_label(loop=loop, x_value=x_value)
            plot.create_live_plot(title=self.name, x_label=x_label, y_label="Amplitude")
        self._process_loop(results=results, loop=loop, depth=depth, path=path, plot=plot)
        return results

    def _execute_and_process_results(self, results: Results, path: Path, plot: LivePlot, x_value: float) -> Results:
        """Execute pulse sequence, add results to Results class and plot the probability of being in the ground state.

        Args:
            results (Results): Results class containing all the execution results.
            path (Path): Path where the data is stored.
            plot (LivePlot): LivePlot class used for live plotting.
            x_value (float): X value used in live plotting.

        Returns:
            Results: Results class containing all the execution results.
        """
        result = self._execute(path=path)
        results.add(result=result)
        # FIXME: If executing a list of sequences (example: AllXY), here we only plot the probability of being
        # in the ground state for the last sequence. Find a way to plot all the sequences.
        plot.send_points(x_value=x_value, y_value=np.round(result[-1].probabilities()[0], 4))
        return results

    def _set_x_label(self, loop: Loop, x_value: float) -> str:
        """Create x label for live plotting.

        Args:
            loop (Loop): Loop class.
            x_value (float): X value used in live plotting.

        Returns:
            str: X label.
        """
        x_label = f"{loop.category} {loop.id_}: {loop.parameter} "
        if loop.previous is not None:
            x_label += (
                f"({loop.previous.category} {loop.previous.id_}:" + f"{loop.previous.parameter}={np.round(x_value, 4)})"
            )
        return x_label

    def _process_loop(self, results: Results, loop: Loop, depth: int, path: Path, plot: LivePlot):
        """Loop over the loop range values, change the element's parameter and call the recursive_loop function.

        Args:
            results (Results): Results class containing all the execution results.
            loop (Loop): Loop class containing the the info of a Platform element and one of its parameters and the
            parameter values to loop over.
            depth (int): Depth of the recursive loop.
            path (Path): Path where the data is stored.
            plot (LivePlot): LivePlot class used for live plotting.
        """
        element, _ = self.platform.get_element(category=Category(loop.category), id_=loop.id_)
        leave = loop.previous is False
        with tqdm(total=len(loop.range), position=depth, leave=leave) as pbar:
            for value in loop.range:
                pbar.set_description(f"{loop.parameter}: {value} ")
                pbar.update()
                element.set_parameter(parameter=loop.parameter, value=value)
                results = self.recursive_loop(
                    loop=loop.loop, results=results, path=path, plot=plot, x_value=value, depth=depth + 1
                )

    def _execute(self, path: Path, plot: LivePlot = None) -> List[Result]:
        """Execute pulse sequences.

        Args:
            results (Results): Results class.

        Returns:
            Results.ExecutionResults: ExecutionResults class.
        """
        if plot is not None:
            plot.create_live_plot(title=self.name, x_label="Sequence idx", y_label="Amplitude")

        return self.execution.run(
            nshots=self.hardware_average,
            repetition_duration=self.repetition_duration,
            software_average=self.software_average,
            plot=plot,
            path=path,
        )

    def set_parameter(self, category: Category | str, id_: int, parameter: Parameter | str, value: float):
        """Set parameter of a platform element.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
            value (float): New value.
        """
        if isinstance(parameter, str):
            parameter = Parameter(parameter)
        if isinstance(category, str):
            category = Category(category)

        # FIXME: Avoid calling self._build_execution twice
        if Category(category) == Category.EXPERIMENT:
            attr_type = type(getattr(self.settings, parameter.value))
            setattr(self.settings, parameter.value, attr_type(value))
            self.execution, self.sequences = self._build_execution(sequence_list=self._initial_sequences)
            return
        self.platform.set_parameter(category=category, id_=id_, parameter=parameter, value=value)
        if Category(category) == Category.PLATFORM:
            self.execution, self.sequences = self._build_execution(sequence_list=self._initial_sequences)

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

    def _build_execution(self, sequence_list: List[Circuit | PulseSequences]) -> Tuple[Execution, List[PulseSequences]]:
        """Build Execution class.

        Args:
            sequence (Circuit | PulseSequence): Sequence of gates/pulses.
        """
        sequences = []
        for sequence in sequence_list:
            if isinstance(sequence, Circuit):
                sequence = CircuitToPulses().translate(
                    circuit=sequence, translation_settings=self.platform.translation_settings
                )
            sequences.append(sequence)
        execution = EXECUTION_BUILDER.build(platform=self.platform, pulse_sequences=sequences)
        return execution, sequences

    def _create_folder(self) -> Path:
        """Create folder where the data will be saved.

        Returns:
            Path: Path to folder.
        """
        now = datetime.now()
        # create folder
        path = (
            Path(self.folderpath)
            / f"{now.year}{now.month:02d}{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}_{self.name}"
        )
        if not os.path.exists(path):
            os.makedirs(path)

        return path

    def _create_results_file(self, path: Path):
        """Create 'results.yml' file.

        Args:
            path (Path): Path to data folder.
        """
        data = {
            YAML.SOFTWARE_AVERAGE: self.software_average,
            YAML.NUM_SEQUENCES: self.execution.num_sequences,
            YAML.SHAPE: [] if self.loop is None else self.loop.shape,
            YAML.RESULTS: None,
        }
        with open(file=path / RESULTS_FILENAME, mode="w", encoding="utf-8") as results_file:
            yaml.dump(data=data, stream=results_file, sort_keys=False)

    def _dump_experiment_data(self, path: Path):
        """Dump experiment data.

        Args:
            path (Path): Path to data folder.
        """
        with open(file=path / EXPERIMENT_FILENAME, mode="w", encoding="utf-8") as experiment_file:
            yaml.dump(data=self.to_dict(), stream=experiment_file, sort_keys=False)

    @property
    def folderpath(self):
        """Experiment 'path' property.

        Returns:
            Path: Path to the data folder.
        """
        folderpath = os.environ.get(DATA, None)
        if folderpath is None:
            folderpath = str(Path(__file__).parent.parent / DATA_FOLDERNAME)
        return folderpath

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

    def to_dict(self):
        """Convert Experiment into a dictionary.

        Returns:
            dict: Dictionary representation of the Experiment class.
        """
        return {
            YAML.PLATFORM: self.platform.to_dict(),
            YAML.SETTINGS: asdict(self.settings),
            YAML.SEQUENCES: [sequence.to_dict() for sequence in self.sequences],
            LOOP.LOOP: self.loop.to_dict() if self.loop is not None else None,
            YAML.NAME: self.name,
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load experiment from dictionary.

        Args:
            dictionary (dict): Dictionary description of an experiment.
        """
        settings = cls.ExperimentSettings(**dictionary[YAML.SETTINGS])
        platform = Platform(runcard_schema=RuncardSchema(**dictionary[YAML.PLATFORM]))
        sequences = [PulseSequences.from_dict(settings) for settings in dictionary[YAML.SEQUENCES]]
        loop = dictionary[LOOP.LOOP]
        loop = Loop(**loop) if loop is not None else None
        experiment_name = dictionary[YAML.NAME]
        return Experiment(
            sequences=sequences,
            loop=loop,
            platform_name=platform.name,
            settings=settings,
            experiment_name=experiment_name,
        )
