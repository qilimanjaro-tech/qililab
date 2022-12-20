""" Experiment class."""
import copy
import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

from qibo.core.circuit import Circuit
from tqdm.auto import tqdm

from qililab.chip import Node
from qililab.config import __version__, logger
from qililab.constants import EXPERIMENT, RUNCARD
from qililab.execution import EXECUTION_BUILDER, Execution, ExecutionPreparation
from qililab.platform.platform import Platform
from qililab.pulse import CircuitToPulses, PulseSchedule
from qililab.remote_connection import RemoteAPI
from qililab.result.result import Result
from qililab.result.results import Results
from qililab.settings import RuncardSchema
from qililab.typings.enums import Category, Instrument, Parameter
from qililab.typings.execution import ExecutionOptions
from qililab.typings.experiment import ExperimentOptions
from qililab.utils.live_plot import LivePlot
from qililab.utils.loop import Loop


@dataclass
class Experiment:
    """Experiment class"""

    platform: Platform
    circuits: list[Circuit] = field(default_factory=list)
    pulse_schedules: list[PulseSchedule] = field(default_factory=list)
    options: ExperimentOptions = field(default=ExperimentOptions())
    _results_path: Path = field(init=False)
    _plot: LivePlot = field(init=False)
    _results: Results = field(init=False)
    _execution: Execution = field(init=False)
    _execution_preparation: ExecutionPreparation = field(init=False)
    _schedules: list[PulseSchedule] = field(init=False)
    _execution_ready: bool = field(init=False)
    _remote_saved_experiment_id: int = field(init=False)

    def __post_init__(self):
        """prepares the Experiment class"""
        self._remote_api = (
            RemoteAPI(
                connection=self.options.connection,
                device_id=self.options.device_id,
                manual_override=self.options.remote_device_manual_override,
            )
            if self.platform.remote_api is None
            else self.platform.remote_api
        )
        self._execution, self._schedules = self._build_execution(
            circuits=self.circuits,
            pulse_schedules=self.pulse_schedules,
            execution_options=self.options.execution_options,
        )
        self._execution_preparation = ExecutionPreparation(remote_api=self._remote_api, options=self.options)
        self._execution_not_prepared()

    @property
    def software_average(self):
        """Experiment 'software_average' property.
        Returns:
            int: settings.software_average.
        """
        return self.options.settings.software_average

    @property
    def hardware_average(self):
        """Experiment 'hardware_average' property.
        Returns:
            int: settings.hardware_average.
        """
        return self.options.settings.hardware_average

    @property
    def repetition_duration(self):
        """Experiment 'repetition_duration' property.
        Returns:
            int: settings.repetition_duration.
        """
        return self.options.settings.repetition_duration

    @property
    def execution_ready(self):
        """checks if execution has already been prepared"""
        return self._execution_ready

    def _execution_not_prepared(self):
        """Sets the execution state to not be prepared"""
        self._execution_ready = False

    def execution_finished(self):
        """Finishes the execution"""
        self._execution_not_prepared()
        self._remote_api.release_remote_device()

    def prepare_execution_and_load_schedule(self, schedule_index_to_load: int = 0) -> None:
        """Prepares the experiment with the following steps:
          - Create results data files and Results object
          - Serializes the Experiment information to a file
          - Creates Live Plotting (if required)
          - uploads the specified schedule to the AWGs (if buses admit that)

        Args:
            schedule_index_to_load (int, optional): specific schedule to load. Defaults to 0.
        """
        (
            self._plot,
            self._results,
            self._results_path,
            self._execution_ready,
        ) = self._execution_preparation.prepare_execution_and_load_schedule(
            execution=self._execution,
            experiment_serialized=self.to_dict(),
            schedule_index_to_load=schedule_index_to_load,
        )

    def execute(self) -> Results:
        """Run execution."""
        if not self.execution_ready:
            (
                self._plot,
                self._results,
                self._results_path,
                self._execution_ready,
            ) = self._execution_preparation.prepare_execution(
                num_schedules=self._execution.num_schedules, experiment_serialized=self.to_dict()
            )

        with self._execution:
            self._execute_all_circuits_or_schedules()

        if self.options.remote_save:
            self.remote_save_experiment()

        return self._results

    def remote_save_experiment(self):
        """sends the remote save_experiment request using the provided remote connection"""
        self._remote_saved_experiment_id = self._remote_api.connection.save_experiment(
            name=self.options.name,
            descitpion=self.options.description,
            experiment_dict=self.to_dict(),
            results_dict=self._results.to_dict(),
            device_id=self.options.device_id,
            user_id=self._remote_api.connection.user_id,
            qililab_version=__version__,
            favourite=False,
        )
        return self._remote_saved_experiment_id

    def _execute_all_circuits_or_schedules(self):
        """runs the circuits (or schedules) passed as input times software average"""
        try:
            disable = self._execution.num_schedules == 1
            for idx, _ in itertools.product(
                tqdm(range(self._execution.num_schedules), desc="Sequences", leave=False, disable=disable),
                range(self.software_average),
            ):
                self._execute_recursive_loops(
                    results=self._results,
                    schedule_index_to_load=idx,
                    loops=self.options.loops,
                    path=self._results_path,
                    plot=self._plot,
                )
            self.execution_finished()

        except (
            AttributeError,
            ValueError,
            KeyboardInterrupt,
            KeyError,
            TimeoutError,
            TypeError,
        ) as error:  # pylint: disable=broad-except
            self.execution_finished()
            logger.error("%s: %s", type(error).__name__, str(error))
            raise error

    def _execute_recursive_loops(
        self,
        results: Results,
        schedule_index_to_load: int,
        loops: List[Loop] | None,
        path: Path,
        plot: LivePlot,
        depth: int = 0,
    ):
        """Loop over all the range values defined in the Loop class and change the parameters of the chosen instruments.

        Args:
            loop (Loop | None): Loop class containing the the info of a Platform element and one of its parameters and
            the parameter values to loop over.
            results (Results): Results class containing all the execution results.
            path (Path): Path where the data is stored.
            plot (LivePlot): LivePlot class used for live plotting.
            depth (int): Depth of the recursive loop. Defaults to 0.
        """
        if loops is None or len(loops) <= 0:
            result = self._generate_program_upload_and_execute(
                schedule_index_to_load=schedule_index_to_load, path=path, plot=plot
            )
            if result is not None:
                results.add(result)
            return

        self._process_loops(
            results=results,
            schedule_index_to_load=schedule_index_to_load,
            loops=loops,
            depth=depth,
            path=path,
            plot=plot,
        )

    def _process_loops(
        self, results: Results, schedule_index_to_load: int, loops: List[Loop], depth: int, path: Path, plot: LivePlot
    ):
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

                self._execute_recursive_loops(
                    schedule_index_to_load=schedule_index_to_load,
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
            parameter=loop.parameter,
            value=value,
            channel_id=loop.channel_id,
        )

    def _get_platform_elements_from_loops(self, loops: List[Loop]):
        """get platform elements from loops"""
        return [self._get_platform_element_from_one_loop(loop=loop) for loop in loops]

    def _get_platform_element_from_one_loop(self, loop: Loop):
        """get platform element from one loop"""
        return self.platform.get_element(alias=loop.alias)

    def _generate_program_upload_and_execute(
        self, schedule_index_to_load: int, path: Path, plot: LivePlot = None
    ) -> Result | None:
        """Execute one pulse schedule.

        Args:
            path (Path): Path to data folder.
            plot (LivePlot | None): Live plot

        Returns:
            Result: Result object for one program execution.
        """
        self._execution.generate_program_and_upload(
            schedule_index_to_load=schedule_index_to_load,
            nshots=self.hardware_average,
            repetition_duration=self.repetition_duration,
            path=path,
        )
        return self._execution.run(plot=plot, path=path)

    def set_parameter(
        self,
        parameter: Parameter,
        value: float,
        alias: str,
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
        if element is None:
            self.platform.set_parameter(
                alias=alias,
                parameter=Parameter(parameter),
                value=value,
                channel_id=channel_id,
            )
        elif isinstance(element, RuncardSchema.PlatformSettings):
            element.set_parameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id)
        else:
            element.set_parameter(parameter=parameter, value=value, channel_id=channel_id)  # type: ignore

        if alias in ([Category.PLATFORM.value] + self.platform.gate_names):
            self._execution, self._schedules = self._build_execution(
                circuits=self.circuits,
                pulse_schedules=self.pulse_schedules,
                execution_options=self.options.execution_options,
            )

    def draw(self, resolution: float = 1.0, idx: int = 0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        return self._execution.draw(resolution=resolution, idx=idx)

    def _build_execution(
        self, circuits: list[Circuit], pulse_schedules: list[PulseSchedule], execution_options: ExecutionOptions
    ) -> Tuple[Execution, List[PulseSchedule]]:
        """Build Execution class.

        Args:
            sequence (Circuit | PulseSequence): Sequence of gates/pulses.
            options (ExecutionOptions): Execution options
        """
        pulse_schedules_input = copy.deepcopy(pulse_schedules)
        if circuits is not None and circuits:
            translator = CircuitToPulses(settings=self.platform.settings)
            pulse_schedules_input += translator.translate(circuits=circuits, chip=self.platform.chip)
        execution = EXECUTION_BUILDER.build(
            platform=self.platform, pulse_schedules=pulse_schedules_input, execution_options=execution_options
        )
        return execution, pulse_schedules

    def to_dict(self):
        """Convert Experiment into a dictionary.

        Returns:
            dict: Dictionary representation of the Experiment class.
        """
        return {
            RUNCARD.PLATFORM: self.platform.to_dict(),
            EXPERIMENT.CIRCUITS: [circuit.to_qasm() for circuit in self.circuits],
            EXPERIMENT.PULSE_SCHEDULES: [pulse_schedule.to_dict() for pulse_schedule in self.pulse_schedules],
            EXPERIMENT.OPTIONS: self.options.to_dict(),
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load experiment from dictionary.

        Args:
            dictionary (dict): Dictionary description of an experiment.
        """

        platform = Platform(runcard_schema=RuncardSchema(**dictionary[RUNCARD.PLATFORM]))
        circuits = (
            [Circuit.from_qasm(settings) for settings in dictionary[EXPERIMENT.CIRCUITS]]
            if EXPERIMENT.CIRCUITS in dictionary
            else []
        )
        pulse_schedules = (
            [PulseSchedule.from_dict(settings) for settings in dictionary[EXPERIMENT.PULSE_SCHEDULES]]
            if EXPERIMENT.PULSE_SCHEDULES in dictionary
            else []
        )
        experiment_options = ExperimentOptions.from_dict(dictionary[EXPERIMENT.OPTIONS])
        return Experiment(
            platform=platform,
            circuits=circuits,
            pulse_schedules=pulse_schedules,
            options=experiment_options,
        )

    def __str__(self):
        """String representation of an experiment."""
        return (
            f"Experiment {self.options.name}:\n"
            + f"{str(self.platform)}\n"
            + f"{str(self.circuits)}\n"
            + f"{str(self.pulse_schedules)}\n"
            + f"{str(self.options)}"
        )
