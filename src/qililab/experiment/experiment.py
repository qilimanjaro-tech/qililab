""" Experiment class."""
import itertools
from pathlib import Path
from typing import List, Tuple

from qibo.models.circuit import Circuit
from tqdm.auto import tqdm

from qililab.chip import Node
from qililab.config import __version__, logger
from qililab.constants import EXPERIMENT, RUNCARD
from qililab.execution import EXECUTION_BUILDER, Execution
from qililab.platform.platform import Platform
from qililab.pulse import CircuitToPulses, PulseSchedule
from qililab.result.result import Result
from qililab.result.results import Results
from qililab.settings import RuncardSchema
from qililab.typings.enums import Instrument, Parameter
from qililab.typings.experiment import ExperimentOptions
from qililab.utils.live_plot import LivePlot
from qililab.utils.loop import Loop

from .prepare_results import prepare_results


class Experiment:
    """Experiment class"""

    # Specify the types of the attributes that are not defined during initialization
    execution: Execution
    results: Results
    results_path: Path
    _plot: LivePlot
    _remote_id: int

    def __init__(
        self,
        platform: Platform,
        circuits: List[Circuit] | None = None,
        pulse_schedules: List[PulseSchedule] | None = None,
        options: ExperimentOptions = ExperimentOptions(),
    ):
        self.platform = platform
        self.circuits = circuits or []
        self.pulse_schedules = pulse_schedules or []
        self.options = options

    def connect(self):
        """Connects to the instruments and blocks the device."""
        self.platform.connect(
            connection=self.options.connection,
            device_id=self.options.device_id,
            manual_override=self.options.remote_device_manual_override,
        )

    def initial_setup(self):
        """Configure each instrument with the values defined in the runcard."""
        self.platform.initial_setup()

    def build_execution(self):
        """Translates the list of circuits to pulse sequences (if needed), creates the ``Execution`` class,
        generates the live plotting and prepares the `Results` class and the `results.yml` file.
        """
        # Translate circuits into pulses if needed
        if self.circuits:
            translator = CircuitToPulses(settings=self.platform.settings)
            self.pulse_schedules += translator.translate(circuits=self.circuits, chip=self.platform.chip)
        # Build ``Execution`` class
        self.execution = EXECUTION_BUILDER.build(platform=self.platform, pulse_schedules=self.pulse_schedules)
        # Generate live plotting
        self._plot = LivePlot(
            connection=self.options.connection,
            loops=self.options.loops,
            plot_y_label=self.options.plot_y_label,
            num_schedules=self.execution.num_schedules,
            title=self.options.name,
        )
        # Prepares the results
        self.results, self.results_path = prepare_results(self.options, self.execution.num_schedules, self.to_dict())

    def run(self):
        """This method is responsible for:
        * Looping over all the given circuits, loops and/or software averages. And for each loop:
            * Generating and uploading the program corresponding to the circuit.
            * Executing the circuit.
            * Saving the results to the ``results.yml`` file.
            * Sending the data to the live plotting (if asked to).
            * Save the results to the ``results`` attribute.
            * Save the results to the remote database (if asked to).
        """
        if not hasattr(self, "execution"):
            raise ValueError("Please build the execution before running an experiment.")
        num_schedules = self.execution.num_schedules
        for idx, _ in itertools.product(
            tqdm(range(num_schedules), desc="Sequences", leave=False, disable=num_schedules == 1),
            range(self.software_average),
        ):
            self._execute_recursive_loops(loops=self.options.loops, idx=idx)

        if self.options.remote_save:
            self.remote_save_experiment()

    def turn_on_instruments(self):
        """Turn on instruments."""
        if not hasattr(self, "execution"):
            raise ValueError("Please build the execution before turning on the instruments.")
        self.execution.turn_on_instruments()

    def turn_off_instruments(self):
        """Turn off instruments."""
        if not hasattr(self, "execution"):
            raise ValueError("Please build the execution before turning off the instruments.")
        self.execution.turn_off_instruments()

    def disconnect(self):
        """Disconnects from the instruments and releases the device."""
        self.platform.disconnect(self.options.connection, self.options.device_id)

    def execute(self) -> Results:
        """Runs the whole execution pipeline, which includes the following steps:

            * Connect to the instruments.
            * Apply settings of the runcard to the instruments.
            * Translate circuit into pulses and create the ``Execution`` class.
            * Turn on instruments.
            * Create the results files & class and connect to live plotting.
            * Runs the experiment.
            * Turn off instruments.
            * Disconnect from the instruments.
            * Return results.

        Returns:
            Results: execution results
        """
        self.connect()
        self.initial_setup()
        self.build_execution()
        self.turn_on_instruments()
        self.run()
        self.turn_off_instruments()
        self.disconnect()
        return self.results

    def remote_save_experiment(self) -> None:
        """Saves the experiment and the results to the remote database and updates the ``_remote_id`` attribute.

        Raises:
            ValueError: if connection is not specified
        """
        if self.options.connection is None:
            return

        logger.debug("Sending experiment and results to remote database.")
        self._remote_id = self.options.connection.save_experiment(
            name=self.options.name,
            description=self.options.description,
            experiment_dict=self.to_dict(),
            results_dict=self.results.to_dict(),
            device_id=self.options.device_id,
            user_id=self.options.connection.user_id,
            qililab_version=__version__,
            favorite=False,
        )

    def _generate_program_upload_and_execute(self, idx: int) -> Result | None:
        """Given a loop index, generates and uploads the assembly program of the corresponding circuit,
        executes it and returns the results.

        Args:
            idx (int): loop index to execute

        Returns:
            Result: Result object for one program execution.
        """
        self.execution.generate_program_and_upload(
            idx=idx, nshots=self.hardware_average, repetition_duration=self.repetition_duration, path=self.results_path
        )
        return self.execution.run(plot=self._plot, path=self.results_path)

    def _execute_recursive_loops(self, loops: List[Loop] | None, idx: int, depth=0):
        """Loop over all the range values defined in the Loop class and change the parameters of the chosen instruments.

        Args:
            loops (List[Loop]): list of Loop classes containing the info of one or more Platform element and the
            parameter values to loop over.
            idx (int): index of the loop
            depth (int): depth of the recursive loop.
        """
        if loops is None or len(loops) == 0:
            result = self._generate_program_upload_and_execute(idx=idx)
            if result is not None:
                self.results.add(result)
            return

        self._process_loops(loops=loops, idx=idx, depth=depth)

    def _process_loops(self, loops: List[Loop], idx: int, depth: int):
        """Loop over the loop range values, change the element's parameter and call the recursive_loop function.

        Args:
            loops (List[Loop]): list of Loop classes containing the info of one or more Platform element and the
            parameter values to loop over.
            idx (int): index of the loop
            depth (int): depth of the recursive loop.
        """
        is_the_top_loop = all(loop.previous is False for loop in loops)

        with tqdm(total=min(len(loop.range) for loop in loops), position=depth, leave=is_the_top_loop) as pbar:
            loop_ranges = [loop.range for loop in loops]

            for values in zip(*loop_ranges):
                self._update_tqdm_bar(loops=loops, values=values, pbar=pbar)
                filtered_loops, filtered_values = self._filter_loops_values_with_external_parameters(
                    values=values,
                    loops=loops,
                )
                self._update_parameters_from_loops(values=filtered_values, loops=filtered_loops)
                inner_loops = list(filter(None, [loop.loop for loop in loops]))
                self._execute_recursive_loops(idx=idx, loops=inner_loops, depth=depth + 1)

    def _update_tqdm_bar(self, loops: List[Loop], values: Tuple[float], pbar):
        """Updates TQDM bar"""
        description = []
        for value, loop in zip(values, loops):
            parameter_text = (
                loop.alias if loop.parameter == Parameter.EXTERNAL and loop.alias is not None else loop.parameter.value
            )
            description.append(f"{parameter_text}: {value}")
        pbar.set_description(" | ".join(description))
        pbar.update()

    def _filter_loops_values_with_external_parameters(self, values: Tuple[float], loops: List[Loop]):
        """filter loops and values removing those with external parameters"""
        if len(values) != len(loops):
            raise ValueError(f"Values list length: {len(values)} differ from loops list length: {len(loops)}.")
        filtered_loops = loops.copy()
        filtered_values = list(values).copy()
        for idx, loop in enumerate(filtered_loops):
            if loop.parameter == Parameter.EXTERNAL:
                filtered_loops.pop(idx)
                filtered_values.pop(idx)

        return filtered_loops, filtered_values

    def _update_parameters_from_loops(self, values: List[float], loops: List[Loop]):
        """update parameters from loops"""
        elements = [self.platform.get_element(alias=loop.alias) for loop in loops]

        for value, loop, element in zip(values, loops, elements):
            self.set_parameter(
                element=element,
                alias=loop.alias,
                parameter=loop.parameter,
                value=value,
                channel_id=loop.channel_id,
            )

    def set_parameter(
        self,
        parameter: Parameter,
        value: float | str | bool,
        alias: str,
        element: RuncardSchema.PlatformSettings | Node | Instrument | None = None,
        channel_id: int | None = None,
    ):
        """Set parameter of a platform element.

        Args:
            parameter (Parameter): name of the parameter to change
            value (float): new value
            alias (str): alias of the element that contains the given parameter
            channel_id (int | None): channel id
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

    def draw(self, resolution: float = 1.0, idx: int = 0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        if not hasattr(self, "execution"):
            raise ValueError("Please build the execution before drawing the experiment.")
        return self.execution.draw(resolution=resolution, idx=idx)

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
