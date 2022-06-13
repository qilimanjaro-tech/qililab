"""HardwareExperiment class."""


import contextlib
import copy
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import numpy as np
from qibo.core.circuit import Circuit
from qiboconnection.api import API
from tqdm.auto import tqdm

from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform import Platform, PlatformSchema
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

    def __init__(
        self,
        sequences: List[Circuit | PulseSequences] | Circuit | PulseSequences,
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
            with contextlib.suppress(KeyboardInterrupt):
                self._execute_loop(results=results, plot=plot, path=path)
        return results

    def _execute_loop(self, results: Results, plot: LivePlot, path: Path):
        """Loop and execute sequence over given Platform parameters.

        Args:
            plot_id (str): Plot ID.

        Returns:
            List[List[Result]]: List containing the results for each loop execution.
        """

        def recursive_loop(loop: Loop | None, x_value: float = 0, depth: int = 0):
            """Loop over all given parameters.

            Args:
                depth (int): Depth of the recursive loop.
                x_value (float): X value.
            """

            if loop is None:
                result = self._execute(path=path)
                results.add(result=result)
                plot.send_points(x_value=x_value, y_value=np.round(result[-1].probabilities()[0], 4))
                return

            if loop.loop is None:
                x_label = f"{loop.category} {loop.id_}: {loop.parameter} "
                if loop.previous is not None:
                    x_label += (
                        f"({loop.previous.category} {loop.previous.id_}:"
                        + f"{loop.previous.parameter}={np.round(x_value, 4)})"
                    )
                plot.create_live_plot(title=self.name, x_label=x_label, y_label="Amplitude")

            element, _ = self.platform.get_element(category=Category(loop.category), id_=loop.id_)
            leave = loop.previous is False
            with tqdm(total=len(loop.range), position=depth, leave=leave) as pbar:
                for value in loop.range:
                    pbar.set_description(f"{loop.parameter}: {value} ")
                    pbar.update()
                    element.set_parameter(parameter=loop.parameter, value=value)
                    recursive_loop(loop=loop.loop, x_value=value, depth=depth + 1)
            return

        if self.loop is None:
            result = self._execute(plot=plot, path=path)
            results.add(result=result)
        else:
            recursive_loop(loop=self.loop)

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

    def draw(self, resolution: float = 1.0, idx: int = 0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self.execution.draw(resolution=resolution, idx=idx)

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
            "software_average": self.software_average,
            "num_sequences": self.execution.num_sequences,
            "shape": [] if self.loop is None else self.loop.shape,
            "results": None,
        }
        with open(file=path / "results.yml", mode="w", encoding="utf8") as results_file:
            yaml.dump(data=data, stream=results_file, sort_keys=False)

    def _dump_experiment_data(self, path: Path):
        """Dump experiment data.

        Args:
            path (Path): Path to data folder.
        """
        with open(file=path / "experiment.yml", mode="w", encoding="utf-8") as experiment_file:
            yaml.dump(data=self.to_dict(), stream=experiment_file, sort_keys=False)

    @property
    def folderpath(self):
        """Experiment 'path' property.

        Returns:
            Path: Path to the data folder.
        """
        folderpath = os.environ.get("DATA", None)
        if folderpath is None:
            folderpath = str(Path(__file__).parent.parent / "data")
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
            "platform": self.platform.to_dict(),
            "settings": asdict(self.settings),
            "sequences": [sequence.to_dict() for sequence in self.sequences],
            "loop": self.loop.to_dict() if self.loop is not None else None,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load experiment from dictionary.

        Args:
            dictionary (dict): Dictionary description of an experiment.
        """
        settings = cls.ExperimentSettings(**dictionary["settings"])
        platform = Platform(platform_schema=PlatformSchema(**dictionary["platform"]))
        sequences = [PulseSequences.from_dict(settings) for settings in dictionary["sequences"]]
        loop = dictionary["loop"]
        loop = Loop(**loop) if loop is not None else None
        name = dictionary["name"]
        return Experiment(
            sequences=sequences,
            loop=loop,
            platform=platform,
            settings=settings,
            name=name,
        )
