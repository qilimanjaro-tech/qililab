"""HardwareExperiment class."""
import copy
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import numpy as np
from qibo.core.circuit import Circuit
from qiboconnection.api import API
from tqdm.auto import tqdm

from qililab.config import logger
from qililab.constants import (
    DATA,
    EXPERIMENT,
    EXPERIMENT_FILENAME,
    LOOP,
    RESULTS_FILENAME,
    YAML,
)
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import Platform, RuncardSchema
from qililab.pulse import CircuitToPulses, Pulses
from qililab.result import Result, Results
from qililab.typings import Category, Instrument, Parameter, yaml
from qililab.utils import LivePlot, Loop


class Experiment:
    """HardwareExperiment class"""

    @dataclass
    class ExperimentSettings:
        """Experiment settings."""

        hardware_average: int = 1024
        software_average: int = 1
        repetition_duration: int = 200000

        def __str__(self):
            """Returns a string representation of the experiment settings."""
            return yaml.dump(asdict(self), sort_keys=False)

    def __init__(
        self,
        sequences: List[Circuit | Pulses] | Circuit | Pulses,
        platform: Platform,
        loop: Loop | None = None,
        settings: ExperimentSettings = ExperimentSettings(),
        name: str = "experiment",
    ):
        self.platform = copy.deepcopy(platform)
        self.name = name
        self.loop = loop
        self.settings = settings
        if not isinstance(sequences, list):
            sequences = [sequences]
        self._initial_sequences = sequences
        self.execution, self.sequences = self._build_execution(sequence_list=self._initial_sequences)

    def execute(self, connection: API | None = None) -> Results:
        """Run execution."""
        path = self._create_folder()
        self._create_results_file(path=path)
        self._dump_experiment_data(path=path)
        plot = LivePlot(connection=connection)
        results = Results(
            software_average=self.software_average, num_sequences=self.execution.num_sequences, loop=self.loop
        )
        with self.execution:
            try:
                self._execute_loop(results=results, plot=plot, path=path)
            except KeyboardInterrupt as error:  # pylint: disable=broad-except
                logger.error("%s: %s", type(error).__name__, str(error))
        return results

    def _execute_loop(self, results: Results, plot: LivePlot, path: Path):
        """Loop and execute sequence over given Platform parameters.

        Args:
            plot (LivePlot): LivePlot class used for live plotting.
            path (Path): Path where the data is stored.

        Returns:
            List[List[Result]]: List containing the results for each loop execution.
        """

        if self.loop is None:
            return results.add(self._execute(plot=plot, path=path))

        return self.recursive_loop(
            loop=self.loop,
            results=results,
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
        x_label = f"{loop.instrument.value} {loop.id_}: {loop.parameter.value} "
        if loop.previous is not None:
            x_label += (
                f"({loop.previous.instrument.value} {loop.previous.id_}:"
                + f"{loop.previous.parameter.value}={np.round(x_value, 4)})"
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
        element, _ = self.platform.get_element(category=Category(loop.instrument.value), id_=loop.id_)
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
            path (Path): Path to data folder.
            plot (LivePlot | None): Live plot

        Returns:
            List[Result]: List of Result object for each pulse sequence.
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

    def set_parameter(self, instrument: Instrument, id_: int, parameter: Parameter, value: float):
        """Set parameter of a platform element.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
            value (float): New value.
        """

        self.platform.set_parameter(
            category=Category(instrument.value), id_=id_, parameter=Parameter(parameter), value=value
        )
        if Instrument(instrument) == Instrument.PLATFORM:
            self.execution, self.sequences = self._build_execution(sequence_list=self._initial_sequences)

    @property
    def parameters(self):
        """Configurable parameters of the platform.

        Returns:
            str: JSON of the platform.
        """
        return str(self.platform)

    def draw(self, resolution: float = 1.0, idx: int = 0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.execution.draw(resolution=resolution, idx=idx)

    def _build_execution(self, sequence_list: List[Circuit | Pulses]) -> Tuple[Execution, List[Pulses]]:
        """Build Execution class.

        Args:
            sequence (Circuit | PulseSequence): Sequence of gates/pulses.
        """
        if isinstance(sequence_list[0], Circuit):
            translator = CircuitToPulses(settings=self.platform.translation_settings)
            sequence_list = translator.translate(circuits=sequence_list, chip=self.platform.chip)
        execution = EXECUTION_BUILDER.build(platform=self.platform, pulses_list=sequence_list)
        return execution, sequence_list

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
            EXPERIMENT.SOFTWARE_AVERAGE: self.software_average,
            EXPERIMENT.NUM_SEQUENCES: self.execution.num_sequences,
            EXPERIMENT.SHAPE: [] if self.loop is None else self.loop.shape,
            LOOP.LOOP: self.loop.to_dict() if self.loop is not None else None,
            EXPERIMENT.RESULTS: None,
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
            raise ValueError("Environment variable DATA is not set.")
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
            EXPERIMENT.SEQUENCES: [sequence.to_dict() for sequence in self.sequences],
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
        sequences = [Pulses.from_dict(settings) for settings in dictionary[EXPERIMENT.SEQUENCES]]
        loop = dictionary[LOOP.LOOP]
        loop = Loop(**loop) if loop is not None else None
        experiment_name = dictionary[YAML.NAME]
        return Experiment(
            sequences=sequences,
            loop=loop,
            platform=platform,
            settings=settings,
            name=experiment_name,
        )
