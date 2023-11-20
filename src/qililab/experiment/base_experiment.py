# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" BaseExperiment class."""
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from threading import Thread

import numpy as np
from qcodes.instrument import Instrument as QcodesInstrument
from ruamel.yaml import YAML
from tqdm.auto import tqdm

from qililab.chip import Node
from qililab.config import __version__, logger
from qililab.constants import DATA, EXPERIMENT, EXPERIMENT_FILENAME, RESULTS_FILENAME, RUNCARD
from qililab.execution import EXECUTION_BUILDER, ExecutionManager
from qililab.platform.platform import Platform
from qililab.result.results import Results
from qililab.settings import Runcard
from qililab.settings.gate_event_settings import GateEventSettings
from qililab.typings.enums import Instrument, Parameter
from qililab.typings.experiment import ExperimentOptions
from qililab.utils.live_plot import LivePlot
from qililab.utils.loop import Loop
from qililab.utils.util_loops import compute_shapes_from_loops


class BaseExperiment(ABC):
    """BaseExperiment class"""

    # Specify the types of the attributes that are not defined during initialization
    execution_manager: ExecutionManager
    results: Results
    results_path: Path | None
    _plot: LivePlot | None
    _remote_id: int

    def __init__(self, platform: Platform, options: ExperimentOptions = ExperimentOptions()):
        self.platform = platform
        self.options = options

    def build_execution(self):
        """Creates the ``ExecutionManager`` class from loops."""
        # Build ``ExecutionManager`` class
        self.execution_manager = EXECUTION_BUILDER.build_from_loops(platform=self.platform, loops=self.options.loops)

    def run(self, save_experiment=True, save_results=True) -> Results:
        """This method is responsible for:
        * Creating the live plotting (if connection is provided).
        * Preparing the `Results` class and the `results.yml` file.
        * Looping over all given loops and/or software averages. And for each loop:
            * Saving the results to the ``results.yml`` file.
            * Sending the data to the live plotting (if asked to).
            * Save the results to the ``results`` attribute.
            * Save the results to the remote database (if asked to).
        """
        # Generate live plotting
        if self.platform.connection is None:
            self._plot = None
        else:
            # TODO: Live plotting should be able to hable num_schedules=0
            self._plot = LivePlot(
                connection=self.platform.connection,
                loops=self.options.loops or [],
                num_schedules=1,
                title=self.options.name,
            )

        if not hasattr(self, "execution_manager"):
            raise ValueError("Please build the execution_manager before running an experiment.")

        # Prepares the results
        self.results, self.results_path = self.prepare_results(
            save_experiment=save_experiment, save_results=save_results
        )

        data_queue: Queue = Queue()  # queue used to store the experiment results
        self._asynchronous_data_handling(queue=data_queue)
        self._execute_recursive_loops(loops=self.options.loops, queue=data_queue)

        if self.options.remote_save:
            self.remote_save_experiment()

        return self.results

    def _asynchronous_data_handling(self, queue: Queue):
        """Starts a thread that asynchronously gets the results from the queue, sends them to the live plot (if any)
        and saves them to a file.

        If no items are received in the queue for 5 seconds, the thread will exit.

        Args:
            queue (Queue): Queue used to store the experiment results.
        """
        timeout = max(5, 10 * self.hardware_average * self.repetition_duration * self.num_bins * 1e-9)

        def _threaded_function():
            """Asynchronous thread."""
            while True:
                try:
                    result = queue.get(timeout=timeout)  # get new result from the queue
                except Empty:
                    return  # exit thread if no results are received for 10 times the duration of the program

                if self._plot is not None:
                    acq = result.acquisitions()
                    i = np.array(acq["i"])
                    q = np.array(acq["q"])
                    amplitude = 20 * np.log10(np.abs(i + 1j * q)).astype(np.float64)
                    self._plot.send_points(value=amplitude[0])

                if self.results_path is not None:
                    with open(file=self.results_path / "results.yml", mode="a", encoding="utf8") as data_file:
                        result_dict = result.to_dict()
                        YAML().dump(data=[result_dict], stream=data_file)

        thread = Thread(target=_threaded_function)
        thread.start()

    def execute(self, save_experiment=True, save_results=True) -> Results:
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
        self.platform.connect()
        self.platform.initial_setup()
        self.build_execution()
        self.platform.turn_on_instruments()
        results = self.run(save_experiment=save_experiment, save_results=save_results)
        self.platform.turn_off_instruments()
        self.platform.disconnect()
        QcodesInstrument.close_all()
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

    @abstractmethod
    def _execute_recursive_loops(self, loops: list[Loop] | None, queue: Queue, depth=0):
        """Loop over all the values defined in the Loop class and change the parameters of the chosen instruments.

        Args:
            loops (list[Loop]): list of Loop classes containing the info of one or more Platform element and the
            parameter values to loop over.
            depth (int): depth of the recursive loop.
        """

    def _process_loops(self, loops: list[Loop], queue: Queue, depth: int):
        """Loop over the loop values, change the element's parameter and call the recursive_loop function.

        Args:
            loops (list[Loop]): list of Loop classes containing the info of one or more Platform element and the
            parameter values to loop over.
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
                self._execute_recursive_loops(loops=inner_loops, queue=queue, depth=depth + 1)

    def _update_tqdm_bar(self, loops: list[Loop], values: tuple[float], pbar):
        """Updates TQDM bar"""
        description = []
        for value, loop in zip(values, loops):
            parameter_text = (
                loop.alias if loop.parameter == Parameter.EXTERNAL and loop.alias is not None else loop.parameter.value
            )
            description.append(f"{parameter_text}: {value}")
        pbar.set_description(" | ".join(description))
        pbar.update()

    def _filter_loops_values_with_external_parameters(self, values: tuple[float, ...], loops: list[Loop]):
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

    def _update_parameters_from_loops(self, values: list[float], loops: list[Loop]):
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
        element: Runcard.GatesSettings | Node | Instrument | None = None,
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
        elif isinstance(element, Runcard.GatesSettings):
            element.set_parameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id)
            self.build_execution()
        elif isinstance(element, list):  # if element is a list of GateEventSettings
            if all(isinstance(element_event, GateEventSettings) for element_event in element):  # type: ignore
                self.platform.set_parameter(alias=alias, parameter=Parameter(parameter), value=value)
                self.build_execution()
        else:
            element.set_parameter(parameter=parameter, value=value, channel_id=channel_id)  # type: ignore
            if parameter == Parameter.DELAY:
                self.build_execution()

    def to_dict(self):
        """Convert BaseExperiment into a dictionary.

        Returns:
            dict: Dictionary representation of the BaseExperiment class.
        """
        return {
            RUNCARD.PLATFORM: self.platform.to_dict(),
            EXPERIMENT.OPTIONS: self.options.to_dict(),
        }

    @classmethod
    @abstractmethod
    def from_dict(cls, dictionary: dict):
        """Load BaseExperiment from dictionary.

        Args:
            dictionary (dict): Dictionary description of an BaseExperiment.
        """

    def __str__(self):
        """String representation of a base experiment."""
        return f"BaseExperiment {self.options.name}:\n" + f"{str(self.platform)}\n" + f"{str(self.options)}"

    @property
    def software_average(self):
        """BaseExperiment 'software_average' property.
        Returns:
            int: settings.software_average.
        """
        return self.options.settings.software_average

    @property
    def hardware_average(self):
        """BaseExperiment 'hardware_average' property.
        Returns:
            int: settings.hardware_average.
        """
        return self.options.settings.hardware_average

    @property
    def num_bins(self):
        """BaseExperiment `num_bins` property.
        Returns
            int: settings.num_bins.
        """
        return self.options.settings.num_bins

    @property
    def repetition_duration(self):
        """BaseExperiment 'repetition_duration' property.
        Returns:
            int: settings.repetition_duration.
        """
        return self.options.settings.repetition_duration

    def prepare_results(self, save_experiment=True, save_results=True) -> tuple[Results, Path | None]:
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

        if save_results or save_experiment:
            # Create the folders & files needed to save the results locally
            results_path = self._path_to_results_folder()
            self._create_results_file(results_path)
            if save_experiment:
                # Dump the experiment data into the created file
                with open(file=results_path / EXPERIMENT_FILENAME, mode="w", encoding="utf-8") as experiment_file:
                    YAML().dump(data=self.to_dict(), stream=experiment_file)
        else:
            results_path = None

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
            YAML().dump(data=data, stream=results_file)
