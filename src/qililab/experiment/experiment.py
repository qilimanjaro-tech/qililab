""" Experiment class."""
import itertools
import os
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import List, Tuple

from qibo.models.circuit import Circuit
from tqdm.auto import tqdm

from qililab.chip import Node
from qililab.config import __version__, logger
from qililab.constants import DATA, EXPERIMENT, EXPERIMENT_FILENAME, RESULTS_FILENAME, RESULTSDATAFRAME, RUNCARD
from qililab.execution import EXECUTION_BUILDER, ExecutionManager
from qililab.platform.platform import Platform
from qililab.pulse import CircuitToPulses, PulseSchedule
from qililab.result.result import Result
from qililab.result.results import Results
from qililab.settings import RuncardSchema
from qililab.typings.enums import Instrument, Parameter
from qililab.typings.experiment import ExperimentOptions
from qililab.typings.yaml_type import yaml
from qililab.utils.live_plot import LivePlot
from qililab.utils.loop import Loop
from qililab.utils.util_loops import compute_shapes_from_loops


class Experiment:
    """Experiment class"""

    # Specify the types of the attributes that are not defined during initialization
    execution_manager: ExecutionManager
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

    def connect(self, manual_override=False):
        """Connects to the instruments and blocks the device."""
        self.platform.connect(manual_override=manual_override)

    def initial_setup(self):
        """Configure each instrument with the values defined in the runcard."""
        self.platform.initial_setup()

    def build_execution(self):
        """Translates the list of circuits to pulse sequences (if needed), creates the ``ExecutionManager`` class,
        and generates the live plotting.
        """
        # Translate circuits into pulses if needed
        if self.circuits:
            translator = CircuitToPulses(settings=self.platform.settings)
            self.pulse_schedules = translator.translate(circuits=self.circuits, chip=self.platform.chip)
        # Build ``ExecutionManager`` class
        self.execution_manager = EXECUTION_BUILDER.build(platform=self.platform, pulse_schedules=self.pulse_schedules)
        # Generate live plotting
        if self.platform.connection is None:
            self._plot = None
        else:
            self._plot = LivePlot(
                connection=self.platform.connection,
                loops=self.options.loops or [],
                num_schedules=len(self.pulse_schedules),
                title=self.options.name,
            )

    def run(self) -> Results:
        """This method is responsible for:
        * Preparing the `Results` class and the `results.yml` file.
        * Looping over all the given circuits, loops and/or software averages. And for each loop:
            * Generating and uploading the program corresponding to the circuit.
            * Executing the circuit.
            * Saving the results to the ``results.yml`` file.
            * Sending the data to the live plotting (if asked to).
            * Save the results to the ``results`` attribute.
            * Save the results to the remote database (if asked to).
        """
        if not hasattr(self, "execution_manager"):
            raise ValueError("Please build the execution_manager before running an experiment.")
        # Prepares the results
        self.results, self.results_path = self.prepare_results()
        num_schedules = self.execution_manager.num_schedules

        data_queue: Queue = Queue()  # queue used to store the experiment results
        self._asynchronous_data_handling(queue=data_queue)

        for idx, _ in itertools.product(
            tqdm(range(num_schedules), desc="Sequences", leave=False, disable=num_schedules == 1),
            range(self.software_average),
        ):
            self._execute_recursive_loops(loops=self.options.loops, idx=idx, queue=data_queue)

        if self.options.remote_save:
            self.remote_save_experiment()

        return self.results

    def _asynchronous_data_handling(self, queue: Queue):
        """Starts a thread that asynchronously gets the results from the queue, sends them to the live plot (if any)
        and saves them to a file.

        If no items are received in the queue for 5 seconds, the thread will exit.

        Args:
            queue (Queue): Queue used to store the experiment results.
            path (Path): Path where the results will be saved.
            plot (LivePlot, optional): Live plot to send the results to. Defaults to None.
        """

        def _threaded_function():
            """Asynchronous thread."""
            while True:
                try:
                    result = queue.get(
                        timeout=self.hardware_average * self.repetition_duration * 1e-8
                    )  # get new result from the queue
                except Empty:
                    return  # exit thread if no results are received for 10 times the duration of the program

                if self._plot is not None:
                    probs = result.probabilities()
                    # get zero prob and converting to a float to plot the value
                    # is a numpy.float32, so it is needed to convert it to float
                    if len(probs) > 0:
                        zero_prob = float(probs[RESULTSDATAFRAME.P0].iloc[0])
                        self._plot.send_points(value=zero_prob)
                with open(file=self.results_path / "results.yml", mode="a", encoding="utf8") as data_file:
                    result_dict = result.to_dict()
                    yaml.safe_dump(data=[result_dict], stream=data_file, sort_keys=False)

        thread = Thread(target=_threaded_function)
        thread.start()

    def compile(self) -> List[dict]:
        """Returns a dictionary containing the compiled programs of each bus for each circuit / pulse schedule of the
        experiment.

        Returns:
            List[dict]: List of dictionaries, where each dictionary has a bus alias as keys and a list of
                compiled sequences as values.
        """
        if not hasattr(self, "execution_manager"):
            raise ValueError("Please build the execution_manager before compilation.")
        return [
            self.execution_manager.compile(schedule_idx, self.hardware_average, self.repetition_duration)
            for schedule_idx in range(len(self.pulse_schedules))
        ]

    def turn_on_instruments(self):
        """Turn on instruments."""
        if not hasattr(self, "execution_manager"):
            raise ValueError("Please build the execution_manager before turning on the instruments.")
        self.execution_manager.turn_on_instruments()

    def turn_off_instruments(self):
        """Turn off instruments."""
        if not hasattr(self, "execution_manager"):
            raise ValueError("Please build the execution_manager before turning off the instruments.")
        self.execution_manager.turn_off_instruments()

    def disconnect(self):
        """Disconnects from the instruments and releases the device."""
        self.platform.disconnect()

    def execute(self) -> Results:
        """Runs the whole execution pipeline, which includes the following steps:

            * Connect to the instruments.
            * Apply settings of the runcard to the instruments.
            * Translate circuit into pulses and create the ``ExecutionManager`` class.
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
        results = self.run()
        self.turn_off_instruments()
        self.disconnect()
        return results

    def remote_save_experiment(self) -> None:
        """Saves the experiment and the results to the remote database and updates the ``_remote_id`` attribute.

        Raises:
            ValueError: if connection is not specified
        """
        if self.platform.connection is None:
            return

        logger.debug("Sending experiment and results to remote database.")
        self._remote_id = self.platform.connection.save_experiment(
            name=self.options.name,
            description=self.options.description,
            experiment_dict=self.to_dict(),
            results_dict=self.results.to_dict(),
            device_id=self.platform.device_id,
            user_id=self.platform.connection.user_id,
            qililab_version=__version__,
            favorite=False,
        )

    def _execute_recursive_loops(self, loops: List[Loop] | None, idx: int, queue: Queue, depth=0):
        """Loop over all the values defined in the Loop class and change the parameters of the chosen instruments.

        Args:
            loops (List[Loop]): list of Loop classes containing the info of one or more Platform element and the
            parameter values to loop over.
            idx (int): index of the circuit to execute
            depth (int): depth of the recursive loop.
        """
        if loops is None or len(loops) == 0:
            self.execution_manager.compile(
                idx=idx, nshots=self.hardware_average, repetition_duration=self.repetition_duration
            )
            self.execution_manager.upload()
            result = self.execution_manager.run(queue)
            if result is not None:
                self.results.add(result)
            return

        self._process_loops(loops=loops, idx=idx, queue=queue, depth=depth)

    def _process_loops(self, loops: List[Loop], idx: int, queue: Queue, depth: int):
        """Loop over the loop values, change the element's parameter and call the recursive_loop function.

        Args:
            loops (List[Loop]): list of Loop classes containing the info of one or more Platform element and the
            parameter values to loop over.
            idx (int): index of the circuit to execute
            depth (int): depth of the recursive loop.
        """
        is_the_top_loop = all(loop.previous is False for loop in loops)

        with tqdm(total=min(len(loop.values) for loop in loops), position=depth, leave=is_the_top_loop) as pbar:
            loop_ranges = [loop.values for loop in loops]

            for values in zip(*loop_ranges):
                self._update_tqdm_bar(loops=loops, values=values, pbar=pbar)
                filtered_loops, filtered_values = self._filter_loops_values_with_external_parameters(
                    values=values,
                    loops=loops,
                )
                self._update_parameters_from_loops(values=filtered_values, loops=filtered_loops)
                inner_loops = list(filter(None, [loop.loop for loop in loops]))
                self._execute_recursive_loops(idx=idx, loops=inner_loops, queue=queue, depth=depth + 1)

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
                element=element, alias=loop.alias, parameter=loop.parameter, value=value, channel_id=loop.channel_id
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
            self.platform.set_parameter(alias=alias, parameter=Parameter(parameter), value=value, channel_id=channel_id)
        elif isinstance(element, RuncardSchema.PlatformSettings):
            element.set_parameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id)
            self.build_execution()
        elif isinstance(element, RuncardSchema.PlatformSettings.GateSettings):
            element.set_parameter(parameter=parameter, value=value)
            self.build_execution()
        else:
            element.set_parameter(parameter=parameter, value=value, channel_id=channel_id)  # type: ignore

    def draw(self, resolution: float = 1.0, idx: int = 0):
        """Return figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        if not hasattr(self, "execution_manager"):
            raise ValueError("Please build the execution_manager before drawing the experiment.")
        return self.execution_manager.draw(resolution=resolution, idx=idx)

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

    def prepare_results(self) -> tuple[Results, Path]:
        """Creates the ``Results`` class, creates the ``results.yml`` file where the results will be saved, and dumps
        the experiment data into this file.

        Args:
            options (ExperimentOptions): options of the experiment
            num_schedules (int): number of schedules
            experiment_serialized (dict): dictionary representing the current experiment

        Returns:
            tuple[Results, Path]: a tuple containing the ``Results`` class and the path to the ``results.yml`` file
        """
        # Create the ``Results`` class
        results = Results(
            software_average=self.options.settings.software_average,
            num_schedules=self.execution_manager.num_schedules,
            loops=self.options.loops,
        )
        # Create the folders & files needed to save the results locally
        results_path = self._path_to_results_folder()
        self._create_results_file(results_path)

        # Dump the experiment data into the created file
        with open(file=results_path / EXPERIMENT_FILENAME, mode="w", encoding="utf-8") as experiment_file:
            yaml.dump(data=self.to_dict(), stream=experiment_file, sort_keys=False)

        return results, results_path

    def _path_to_results_folder(self) -> Path:
        """Creates a folder for the current day (if needed), creates another folder for the current timestamp
        (if needed) and returns the path to this last folder.

        Args:
            name (str): name to identify the folder besides the timestamp

        Returns:
            Path: Path to folder.
        """
        # Timestamp
        now = datetime.now()

        # Get path to DATA folder from environment
        daily_path = os.environ.get(DATA, None)
        if daily_path is None:
            raise ValueError("Environment variable DATA is not set.")

        # Generate path to the daily folder
        daily_path = Path(daily_path) / f"{now.year}{now.month:02d}{now.day:02d}"  # type: ignore

        # Check if folder exists, if not create one
        if not os.path.exists(daily_path):
            os.makedirs(daily_path)

        # Generate path to the results folder
        now_path = daily_path / f"{now.hour:02d}{now.minute:02d}{now.second:02d}_{self.options.name}"  # type: ignore

        # Check if folder exists, if not create one
        if not os.path.exists(now_path):
            os.makedirs(now_path)

        return now_path

    def _create_results_file(self, path: Path):
        """Create 'results.yml' file that contains all the information about the current experiment.

        Args:
            path (Path): Path to data folder.
        """

        data = {
            EXPERIMENT.SOFTWARE_AVERAGE: self.options.settings.software_average,
            EXPERIMENT.NUM_SCHEDULES: self.execution_manager.num_schedules,
            EXPERIMENT.SHAPE: [] if self.options.loops is None else compute_shapes_from_loops(loops=self.options.loops),
            EXPERIMENT.LOOPS: [loop.to_dict() for loop in self.options.loops]
            if self.options.loops is not None
            else None,
            EXPERIMENT.RESULTS: None,
        }
        with open(file=path / RESULTS_FILENAME, mode="w", encoding="utf-8") as results_file:
            yaml.dump(data=data, stream=results_file, sort_keys=False)
