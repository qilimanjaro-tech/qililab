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

""" Experiment class."""
import copy
import itertools
from queue import Queue

from qibo.models.circuit import Circuit
from tqdm.auto import tqdm

from qililab.chip import Node
from qililab.circuit_transpiler import CircuitTranspiler
from qililab.config import __version__
from qililab.constants import EXPERIMENT, RUNCARD
from qililab.execution import EXECUTION_BUILDER
from qililab.experiment.base_experiment import BaseExperiment
from qililab.platform.platform import Platform
from qililab.pulse import PulseSchedule
from qililab.result.results import Results
from qililab.settings import Runcard
from qililab.typings.enums import Instrument, Parameter
from qililab.typings.experiment import ExperimentOptions
from qililab.utils.live_plot import LivePlot
from qililab.utils.loop import Loop


class Experiment(BaseExperiment):
    """Experiment class"""

    def __init__(
        self,
        platform: Platform,
        circuits: list[Circuit] | None = None,
        pulse_schedules: list[PulseSchedule] | None = None,
        options: ExperimentOptions = ExperimentOptions(),
    ):
        self.circuits = circuits or []
        self.pulse_schedules = pulse_schedules or []
        super().__init__(platform=platform, options=options)

    def build_execution(self):
        """Translates the list of circuits to pulse sequences (if needed) and creates the ``ExecutionManager`` class."""
        # Translate circuits into pulses if needed
        if self.circuits:
            transpiler = CircuitTranspiler(platform=self.platform)
            self.pulse_schedules = transpiler.circuit_to_pulses(circuits=self.circuits)
        # Build ``ExecutionManager`` class
        self.execution_manager = EXECUTION_BUILDER.build(platform=self.platform, pulse_schedules=self.pulse_schedules)

    def run(self, save_experiment=True, save_results=True) -> Results:
        """This method is responsible for:

        * Creating the live plotting (if connection is provided).

        * Preparing the `Results` class and the `results.yml` file.

        * Looping over all the given circuits, loops and/or software averages. And for each loop:

            * Generating and uploading the program corresponding to the circuit.

            * Executing the circuit.

            * Saving the results to the ``results.yml`` file.

            * Sending the data to the live plotting (if asked to).

            * Save the results to the ``results`` attribute.

            * Save the results to the remote database (if asked to).
        """
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

        if not hasattr(self, "execution_manager"):
            raise ValueError("Please build the execution_manager before running an experiment.")
        # Prepares the results
        self.results, self.results_path = self.prepare_results(
            save_experiment=save_experiment, save_results=save_results
        )
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

    def _execute_recursive_loops(self, loops: list[Loop] | None, queue: Queue, depth=0, **kwargs):
        """Loop over all the values defined in the Loop class and change the parameters of the chosen instruments.

        Args:
            loops (list[Loop]): list of Loop classes containing the info of one or more Platform element and the
            parameter values to loop over.
            idx (int): index of the circuit to execute
            depth (int): depth of the recursive loop.
            kwargs (dict): optional paramters, valid optional parameters:
                idx (int): index of the circuit to execute
        """
        if "idx" not in kwargs:
            raise ValueError("Parameter 'idx' must be specified")
        idx = copy.deepcopy(kwargs["idx"])

        if loops is None or len(loops) == 0:
            result = self.platform.execute(
                program=self.pulse_schedules[idx],
                num_avg=self.hardware_average,
                repetition_duration=self.repetition_duration,
                num_bins=self.num_bins,
                queue=queue,
            )
            if result is not None:
                self.results.add(result)
            return

        self._process_loops(loops=loops, idx=idx, queue=queue, depth=depth)

    def _process_loops(self, loops: list[Loop], queue: Queue, depth: int, **kwargs):  # pylint: disable=unused-argument
        """Loop over the loop values, change the element's parameter and call the recursive_loop function.

        Args:
            loops (list[Loop]): list of Loop classes containing the info of one or more Platform element and the
            parameter values to loop over.
            depth (int): depth of the recursive loop.
            kwargs (dict): optional paramters, valid optional parameters:
                idx (int): index of the circuit to execute
        """

        if "idx" not in kwargs:
            raise ValueError("Parameter 'idx' must be specified")
        idx = copy.deepcopy(kwargs["idx"])

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

    def compile(self) -> list[dict]:
        """Returns a dictionary containing the compiled programs of each bus for each circuit / pulse schedule of the
        experiment.

        Returns:
            list[dict]: List of dictionaries, where each dictionary has a bus alias as keys and a list of
                compiled sequences as values.
        """
        if not hasattr(self, "execution_manager"):
            raise ValueError("Please build the execution_manager before compilation.")
        return [
            self.platform.compile(schedule, self.hardware_average, self.repetition_duration, self.num_bins)
            for schedule in self.pulse_schedules
        ]

    def draw(
        self,
        real: bool = True,
        imag: bool = True,
        absolute: bool = False,
        modulation: bool = True,
        linestyle: str = "-",
        resolution: float = 1.0,
        idx: int = 0,
    ):
        """Return figure with the waveforms/envelopes sent to each bus.

        You can plot any combination of the real (blue), imaginary (orange) and absolute (green) parts of the function.

        Args:
            real (bool): True to plot the real part of the function, False otherwise. Default to True.
            imag (bool): True to plot the imaginary part of the function, False otherwise. Default to True.
            absolute (bool): True to plot the absolute of the function, False otherwise. Default to False.
            modulation (bool): True to plot the modulated wave form, False for only envelope. Default to True.
            linestyle (str): lineplot ("-", "--", ":"), point plot (".", "o", "x") or any other linestyle matplotlib accepts. Defaults to "-".
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        if not hasattr(self, "execution_manager"):
            raise ValueError("Please build the execution_manager before drawing the experiment.")

        return self.execution_manager.draw(
            real=real,
            imag=imag,
            absolute=absolute,
            modulation=modulation,
            linestyle=linestyle,
            resolution=resolution,
            idx=idx,
        )

    def to_dict(self):
        """Convert Experiment into a dictionary.

        Returns:
            dict: Dictionary representation of the Experiment class.
        """
        exp_dict = super().to_dict()
        exp_dict[EXPERIMENT.CIRCUITS] = [circuit.to_qasm() for circuit in self.circuits]
        exp_dict[EXPERIMENT.PULSE_SCHEDULES] = [pulse_schedule.to_dict() for pulse_schedule in self.pulse_schedules]
        return exp_dict

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load Experiment from dictionary.

        Args:
            dictionary (dict): Dictionary description of a Experiment.
        """

        platform = Platform(runcard=Runcard(**dictionary[RUNCARD.PLATFORM]))
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

    def set_parameter(  # pylint: disable=too-many-arguments
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
        if parameter == Parameter.GATE_PARAMETER:
            for circuit in self.circuits:
                parameters = list(sum(circuit.get_parameters(), ()))
                parameters[int(alias)] = value
                circuit.set_parameters(parameters)
            self.build_execution()
            return
        super().set_parameter(parameter=parameter, value=value, alias=alias, element=element, channel_id=channel_id)

    def __str__(self):
        """String representation of a Experiment."""
        base_exp_str = super().__str__()
        return f"{base_exp_str}\n{str(self.circuits)}\n{str(self.pulse_schedules)}\n"
