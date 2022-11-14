""" Experiment class."""
import copy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Tuple

from qibo.core.circuit import Circuit
from qiboconnection.api import API
from tqdm.auto import tqdm

from qililab.chip import Node
from qililab.config import logger
from qililab.constants import EXPERIMENT, EXPERIMENT_FILENAME, RESULTS_FILENAME, RUNCARD
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform.platform import Platform
from qililab.pulse import CircuitToPulses, PulseSequences
from qililab.remote_connection import RemoteAPI
from qililab.result import Result, Results
from qililab.settings import RuncardSchema
from qililab.typings.enums import Category, Instrument, Parameter
from qililab.typings.yaml_type import yaml
from qililab.utils.live_plot import LivePlot
from qililab.utils.loop import Loop
from qililab.utils.results_data_management import create_results_folder
from qililab.utils.util_loops import compute_shapes_from_loops


class Experiment:
    """Experiment class"""

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
        sequences: List[Circuit | PulseSequences] | Circuit | PulseSequences,
        platform: Platform,
        loops: List[Loop] | None = None,
        settings: ExperimentSettings = ExperimentSettings(),
        connection: API | None = None,
        device_id: int | None = None,
        name: str = "experiment",
        plot_y_label: str | None = None,
    ):
        self.platform = copy.deepcopy(platform)
        self.name = name
        self.loops = loops
        self.settings = settings
        if not isinstance(sequences, list):
            sequences = [sequences]
        self._initial_sequences = sequences
        self.remote_api = RemoteAPI(connection=connection, device_id=device_id)
        self.execution, self.sequences = self._build_execution(sequence_list=self._initial_sequences)
        self.plot_y_label = plot_y_label

    def execute(self) -> Results:
        """Run execution."""
        with self.remote_api:
            path = create_results_folder(name=self.name)
            self._create_results_file(path=path)
            self._dump_experiment_data(path=path)
            plot = LivePlot(
                remote_api=self.remote_api,
                loops=self.loops,
                plot_y_label=self.plot_y_label,
                num_sequences=self.execution.num_sequences,
            )
            results = Results(
                software_average=self.software_average, num_sequences=self.execution.num_sequences, loops=self.loops
            )
            with self.execution:
                try:
                    results = self._recursive_loops(
                        loops=self.loops,
                        results=results,
                        path=path,
                        plot=plot,
                    )
                except KeyboardInterrupt as error:  # pylint: disable=broad-except
                    logger.error("%s: %s", type(error).__name__, str(error))
        return results

    def _recursive_loops(
        self, loops: List[Loop] | None, results: Results, path: Path, plot: LivePlot, depth: int = 0
    ) -> Results:
        """Loop over all the range values defined in the Loop class and change the parameters of the chosen instruments.

        Args:
            loop (Loop | None): Loop class containing the the info of a Platform element and one of its parameters and
            the parameter values to loop over.
            results (Results): Results class containing all the execution results.
            path (Path): Path where the data is stored.
            plot (LivePlot): LivePlot class used for live plotting.
            depth (int): Depth of the recursive loop. Defaults to 0.

        Returns:
            Results: _description_
        """
        if loops is None or len(loops) <= 0:
            # results.add(result=self._execute(path=path, plot=plot))
            return results

        self._process_loops(results=results, loops=loops, depth=depth, path=path, plot=plot)
        return results

    def _process_loops(self, results: Results, loops: List[Loop], depth: int, path: Path, plot: LivePlot):
        """Loop over the loop range values, change the element's parameter and call the recursive_loop function.

        Args:
            results (Results): Results class containing all the execution results.
            loops (List[Loop]): Loop class containing the the info of one or more Platform element and the
            parameter values to loop over.
            depth (int): Depth of the recursive loop.
            path (Path): Path where the data is stored.
            plot (LivePlot): LivePlot class used for live plotting.
        """
        is_the_top_loop = all(loop.previous is False for loop in loops)

        with tqdm(total=self.get_minimum_length_loop(loops=loops), position=depth, leave=is_the_top_loop) as pbar:
            loop_ranges = [loop.range for loop in loops]

            for values in zip(*loop_ranges):
                self._update_tqdm_bar(loops=loops, values=values, pbar=pbar)
                self._update_parameters_from_loops_filtering_external_parameters(values=values, loops=loops)

                results = self._recursive_loops(
                    loops=self._create_loops_from_inner_loops(loops=loops),
                    results=results,
                    path=path,
                    plot=plot,
                    depth=depth + 1,
                )

    def _update_tqdm_bar(self, loops: List[Loop], values: Tuple[float], pbar):
        """Updates TQDM bar"""
        description = [self._set_parameter_text_and_value(value, loop) for value, loop in zip(values, loops)]
        pbar.set_description(" | ".join(description))
        pbar.update()

    def _set_parameter_text_and_value(self, value: float, loop: Loop):
        """set paramater text and value to print on terminal TQDM iterations"""
        parameter_text = (
            loop.alias if loop.parameter == Parameter.EXTERNAL and loop.alias is not None else loop.parameter.value
        )
        return f"{parameter_text}: {value}"

    def get_minimum_length_loop(self, loops: List[Loop]):
        """return the minimum length from all loops"""
        return min(len(loop.range) for loop in loops)

    def _create_loops_from_inner_loops(self, loops: List[Loop]):
        """create sequence of loops from inner loops (if exist)"""
        return list(filter(None, [loop.loop for loop in loops]))

    def _update_parameters_from_loops_filtering_external_parameters(
        self,
        values: Tuple[float],
        loops: List[Loop],
    ):
        """Update parameters from loops filtering those loops that relates to external variables
        not associated to neither platform, instrument, or gates settings
        """
        filtered_loops, filtered_values = self._filter_loops_values_with_external_parameters(
            values=values,
            loops=loops,
        )
        self._update_parameters_from_loops(values=filtered_values, loops=filtered_loops)

    def _filter_loops_values_with_external_parameters(self, values: Tuple[float], loops: List[Loop]):
        """filter loops and values removing those with external paramaters"""
        if len(values) != len(loops):
            raise ValueError(f"Values list length: {len(values)} differ from loops list length: {len(loops)}.")
        filtered_loops = loops.copy()
        filtered_values = list(values).copy()
        for idx, loop in enumerate(filtered_loops):
            filtered_loops, filtered_values = self._filter_loop_value_when_parameters_is_external(
                filtered_loops=filtered_loops,
                filtered_values=filtered_values,
                idx=idx,
                loop=loop,
            )
        return filtered_loops, filtered_values

    def _filter_loop_value_when_parameters_is_external(
        self, filtered_loops: List[Loop], filtered_values: List[float], idx: int, loop: Loop
    ):
        """filter loop value when parameters is external"""
        if loop.parameter == Parameter.EXTERNAL:
            filtered_loops.pop(idx)
            filtered_values.pop(idx)
        return filtered_loops, filtered_values

    def _update_parameters_from_loops(
        self,
        values: List[float],
        loops: List[Loop],
    ):
        """update paramaters from loops"""
        elements = self._get_platform_elements_from_loops(loops=loops)

        for value, loop, element in zip(values, loops, elements):
            self._update_parameter_from_loop(value=value, loop=loop, element=element)

    def _update_parameter_from_loop(
        self, value: float, loop: Loop, element: RuncardSchema.PlatformSettings | Node | Instrument
    ):
        """update parameter from loop"""
        self.set_parameter(
            element=element,
            alias=loop.alias,
            instrument=loop.instrument,
            id_=loop.id_,
            parameter=loop.parameter,
            value=value,
            channel_id=loop.channel_id,
        )

    def _get_platform_elements_from_loops(self, loops: List[Loop]):
        """get platform elements from loops"""
        return [self._get_platform_element_from_one_loop(loop=loop) for loop in loops]

    def _get_platform_element_from_one_loop(self, loop: Loop):
        """get platform element from one loop"""
        return self.platform.get_element(
            alias=loop.alias,
            category=Category(loop.instrument.value) if loop.instrument is not None else None,
            id_=loop.id_,
        )

    def _execute(self, path: Path, plot: LivePlot = None) -> List[Result]:
        """Execute pulse sequences.

        Args:
            path (Path): Path to data folder.
            plot (LivePlot | None): Live plot

        Returns:
            List[Result]: List of Result object for each pulse sequence.
        """
        return self.execution.run(
            nshots=self.hardware_average,
            repetition_duration=self.repetition_duration,
            software_average=self.software_average,
            plot=plot,
            path=path,
        )

    def set_parameter(
        self,
        parameter: Parameter,
        value: float,
        alias: str | None = None,
        instrument: Instrument | None = None,
        id_: int | None = None,
        element: RuncardSchema.PlatformSettings | Node | Instrument | None = None,
        channel_id: int | None = None,
    ):
        """Set parameter of a platform element.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
            value (float): New value.
        """
        # print("Setting parameter")
        # print(f"parameter={parameter}; value={value}; alias={alias}")
        # print(f"instrument={instrument}; id_={id_}; element={element}")
        # print(type(element))
        category = Category(instrument.value) if instrument is not None else None
        if element is None:
            # print("Entered branch 1")
            self.platform.set_parameter(
                alias=alias,
                category=category,
                id_=id_,
                parameter=Parameter(parameter),
                value=value,
                channel_id=channel_id,
            )
        elif isinstance(element, RuncardSchema.PlatformSettings):
            element.set_parameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id)
        else:
            element.set_parameter(parameter=parameter, value=value, channel_id=channel_id)  # type: ignore

        if category == Category.PLATFORM or alias in ([Category.PLATFORM.value] + self.platform.gate_names):
            # print("Rebuild execution")
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
        if isinstance(sequence_list[0], Circuit):
            translator = CircuitToPulses(settings=self.platform.settings)
            sequence_list = translator.translate(circuits=sequence_list, chip=self.platform.chip)
        execution = EXECUTION_BUILDER.build(platform=self.platform, pulse_sequences=sequence_list)
        return execution, sequence_list

    def _create_results_file(self, path: Path):
        """Create 'results.yml' file.

        Args:
            path (Path): Path to data folder.
        """

        data = {
            EXPERIMENT.SOFTWARE_AVERAGE: self.software_average,
            EXPERIMENT.NUM_SEQUENCES: self.execution.num_sequences,
            EXPERIMENT.SHAPE: [] if self.loops is None else compute_shapes_from_loops(loops=self.loops),
            EXPERIMENT.LOOPS: [loop.to_dict() for loop in self.loops] if self.loops is not None else None,
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
            RUNCARD.PLATFORM: self.platform.to_dict(),
            RUNCARD.SETTINGS: asdict(self.settings),
            EXPERIMENT.SEQUENCES: [sequence.to_dict() for sequence in self.sequences],
            EXPERIMENT.LOOPS: [loop.to_dict() for loop in self.loops] if self.loops is not None else None,
            RUNCARD.NAME: self.name,
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load experiment from dictionary.

        Args:
            dictionary (dict): Dictionary description of an experiment.
        """
        settings = cls.ExperimentSettings(**dictionary[RUNCARD.SETTINGS])
        platform = Platform(runcard_schema=RuncardSchema(**dictionary[RUNCARD.PLATFORM]))
        sequences = [PulseSequences.from_dict(settings) for settings in dictionary[EXPERIMENT.SEQUENCES]]
        input_loops = dictionary[EXPERIMENT.LOOPS]
        loops = [Loop(**loop) for loop in input_loops] if input_loops is not None else None
        experiment_name = dictionary[RUNCARD.NAME]
        return Experiment(
            sequences=sequences,
            loops=loops,
            platform=platform,
            settings=settings,
            name=experiment_name,
        )
