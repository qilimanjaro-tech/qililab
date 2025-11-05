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

# mypy: disable-error-code="union-attr, arg-type"
import inspect
import os
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from types import LambdaType
from typing import TYPE_CHECKING, Callable
from uuid import UUID

import numpy as np
from rich.progress import BarColumn, Progress, TaskID, TextColumn, TimeElapsedColumn

from qililab.qprogram.blocks import Average, Block, ForLoop, Loop, Parallel
from qililab.qprogram.experiment import Experiment
from qililab.qprogram.operations import ExecuteQProgram, GetParameter, Measure, Operation, SetParameter
from qililab.qprogram.operations.set_crosstalk import SetCrosstalk
from qililab.qprogram.variable import Variable
from qililab.result.experiment_results_writer import (
    ExperimentDataBaseMetadata,
    ExperimentMetadata,
    ExperimentResultsWriter,
    MeasurementMetadata,
    QProgramMetadata,
    VariableMetadata,
)
from qililab.result.qprogram.qprogram_results import QProgramResults
from qililab.utils.serialization import serialize

if TYPE_CHECKING:
    from qililab.platform.platform import Platform


@dataclass
class VariableInfo:
    """Dataclass to store information of a Variable"""

    uuid: UUID
    label: str
    values: np.ndarray


class ExperimentExecutor:
    """Manages the execution of a quantum experiment.

    The `ExperimentExecutor` class is responsible for orchestrating the execution of a quantum experiment on a given platform. It traverses the experiment's structure, handles loops and operations, and stores the results in real-time to ensure data integrity even in case of interruptions.

    Key responsibilities include:

    - Preparing metadata and loop structures before execution.
    - Managing variables and their scopes within loops and blocks.
    - Executing operations in the correct sequence with proper parameter settings.
    - Streaming results to an HDF5 file using `ExperimentResultsWriter`.

    This class provides a high-level interface to execute complex experiments involving nested loops, parameter sweeps, and qprogram executions, while efficiently managing resources and progress tracking.

    Args:
        platform (Platform): The platform on which the experiment is to be executed.
        experiment (Experiment): The experiment object defining the sequence of operations and loops.
        base_data_path (str): The base directory path where the experiment results will be stored.
        live_plot (bool): Flag that abilitates live plotting. Defaults to False.
        slurm_execution (bool): Flag that defines if the liveplot will be held through Dash or a notebook cell. Defaults to True.
        port_number (int|None): Optional parameter for when slurm_execution is True. It defines the port number of the Dash server. Defaults to None.

    Example:
        .. code-block::

            from qililab.data_management import build_platform
            from qililab.qprogram import Experiment
            from qililab.executor import ExperimentExecutor

            # Initialize the platform
            platform = build_platform(runcard="path/to/runcard.yml")

            # Define your experiment
            experiment = Experiment(label="my_experiment")
            # Add blocks, loops, operations to the experiment
            # ...

            # Set the base data path for storing results
            base_data_path = "/data/experiments"

            # Create the ExperimentExecutor
            executor = ExperimentExecutor(platform=platform, experiment=experiment, base_data_path=base_data_path)

            # Execute the experiment
            results_path = executor.execute()
            print(f"Results saved to {results_path}")

    Note:
        - Ensure that the platform and experiment are properly configured before execution.
        - The results will be saved in a timestamped directory within the `base_data_path`.
    """

    def __init__(
        self,
        platform: "Platform",
        experiment: Experiment,
        live_plot: bool = False,
        slurm_execution: bool = True,
        port_number: int | None = None,
        job_id: int | None = None,
        sample: str | None = None,
        cooldown: str | None = None,
    ):
        self.platform = platform
        self.experiment = experiment
        self._live_plot = live_plot
        self._slurm_execution = slurm_execution
        self._port_number = port_number

        # In case the results are saved in a database, load the correct sample and cooldown.
        self.job_id = job_id
        self.sample = sample
        self.cooldown = cooldown

        # Registry of all variables used in the experiment with their labels and values
        self._all_variables: dict = defaultdict(lambda: {"label": None, "values": {}})

        # Mapping from each Block to the list of variables associated with that block
        self._variables_per_block: dict[Block, list[VariableInfo]] = {}

        # Mapping from each ExecuteQProgram operation to its execution index (order of execution)
        self._qprogram_execution_indices: dict[ExecuteQProgram, int] = {}

        # Variables that uses flux for further processing and saving the right bias
        # TODO: implement a way to save the bias based on the same principle as HW loops Xtalk
        self._flux_variables: dict[str, np.ndarray] = {}

        # Stack to keep track of variables in the experiment context (outside QPrograms)
        self._experiment_variables_stack: list[list[VariableInfo]] = []

        # Stack to keep track of variables within QPrograms
        self._qprogram_variables_stack: list[list[VariableInfo]] = []

        # Counter for the number of QPrograms encountered.
        self._qprogram_index = 0

        # Counter for the number of measurements within a QProgram.
        self._measurement_index = 0

        # Number of shots for averaging measurements. It is updated when an Average block is encountered.
        self._shots = 1

        # Metadata dictionary containing information about the experiment structure and variables.
        self._metadata: ExperimentMetadata

        # DatabaseMetadata dictionary containing information about the experiment structure and variables.
        self._db_metadata: ExperimentDataBaseMetadata | None = None

        # ExperimentResultsWriter object responsible for saving experiment results to file in real-time.
        self._results_writer: ExperimentResultsWriter

    def _prepare_metadata(self, executed_at: datetime):
        """Prepares the loop values and result shape before execution."""

        def traverse_experiment(block: Block):
            """Traverses the blocks to gather loop information and determine result shape."""
            if isinstance(block, (Loop, ForLoop, Parallel)):
                variables = self._get_variables_of_loop(block)

                self._experiment_variables_stack.append(variables)

            # Recursively traverse nested blocks or loops
            for element in block.elements:
                if isinstance(element, Block):
                    traverse_experiment(element)
                # Handle ExecuteQProgram operations and traverse their loops
                if isinstance(element, ExecuteQProgram):
                    if isinstance(element.qprogram, LambdaType):
                        signature = inspect.signature(element.qprogram)
                        call_parameters = {param.name: 0 for param in signature.parameters.values()}
                        qprogram = element.qprogram(**call_parameters)
                        traverse_qprogram(qprogram.body)
                    else:
                        traverse_qprogram(element.qprogram.body)
                    self._qprogram_execution_indices[element] = self._qprogram_index
                    self._measurement_index = 0
                    self._qprogram_index += 1

            if isinstance(block, (Loop, ForLoop, Parallel)):
                del self._experiment_variables_stack[-1]

        def traverse_qprogram(block: Block):
            """Traverses a QProgram to gather loop information."""
            if isinstance(block, (Loop, ForLoop, Parallel)):
                variables = self._get_variables_of_loop(block)

                self._qprogram_variables_stack.append(variables)
            if isinstance(block, Average):
                self._shots = block.shots

            # Recursively handle nested blocks within the QProgram
            for element in block.elements:
                if isinstance(element, Block):
                    traverse_qprogram(element)
                if isinstance(element, Measure):
                    finalize_measurement_structure()

            if isinstance(block, (Loop, ForLoop, Parallel)):
                del self._qprogram_variables_stack[-1]
            if isinstance(block, Average):
                self._shots = 1

        def finalize_measurement_structure():
            """Finalize the structure of a measurement when a Measure operation is encountered."""
            qprogram_name = f"QProgram_{self._qprogram_index}"
            measurement_name = f"Measurement_{self._measurement_index}"

            # Ensure QProgram exists in the structure
            if qprogram_name not in self._metadata["qprograms"]:
                self._metadata["qprograms"][qprogram_name] = QProgramMetadata(
                    variables=[
                        VariableMetadata(label=variable.label, values=variable.values)
                        for sublist in self._experiment_variables_stack
                        for variable in sublist
                    ],
                    dims=[[variable.label for variable in sublist] for sublist in self._experiment_variables_stack],
                    measurements={},
                )

            # Add QProgram loops and the measurement
            self._metadata["qprograms"][qprogram_name]["measurements"][measurement_name] = MeasurementMetadata(
                variables=[
                    VariableMetadata(label=variable.label, values=variable.values)
                    for sublist in self._qprogram_variables_stack
                    for variable in sublist
                ],
                dims=[[variable.label for variable in sublist] for sublist in self._qprogram_variables_stack],
                shape=(
                    *tuple(
                        len(sublist[0].values)
                        for sublist in self._experiment_variables_stack + self._qprogram_variables_stack
                    ),
                    2,
                ),
                shots=self._shots,
            )

            # Increase index of measurements
            self._measurement_index += 1

        self._metadata = ExperimentMetadata(
            platform=serialize(self.platform.to_dict()),
            experiment=serialize(self.experiment),
            executed_at=executed_at,
            execution_time=0.0,
            qprograms={},
        )
        if self.platform.save_experiment_results_in_database:
            if self.job_id is None:
                raise ValueError("Job id has not been defined.")
            self._db_metadata = ExperimentDataBaseMetadata(
                job_id=self.job_id,
                experiment_name=self.experiment.label,
                cooldown=self.cooldown,
                sample_name=self.sample,
            )
        traverse_experiment(self.experiment.body)
        self._all_variables = dict(self._all_variables)

    def _prepare_operations(self, block: Block, progress: Progress):
        """Traverse blocks, store generated Python functions, and return the stored operations."""

        # A mapping from block UUID to the associated Progress TaskID
        task_ids: dict[UUID, TaskID] = {}

        # A list of operations to execute
        operations: list[Callable] = []

        # A mapping from block UUID to the index of the current value of its variable
        self.loop_indices: dict[UUID, int] = {}

        # A mapping from variable UUID to current value of the variable
        current_value_of_variable: dict[UUID, int | float] = {}

        def handle_loop(block: ForLoop | Loop | Parallel) -> list[Callable]:
            """Common logic for handling ForLoop and Loop blocks."""
            loop_operations: list[Callable] = []

            # Determine loop parameters based on the type of block
            label = ",".join([variable.label for variable in self._variables_per_block[block]])
            shape = self._variables_per_block[block][0].values.shape[-1]

            # Create the progress bar for the loop
            def create_progress_bar():
                total_iterations = shape
                loop_task_id = progress.add_task(f"Looping over {label}", total=total_iterations)
                task_ids[block.uuid] = loop_task_id  # Store the task ID associated with this loop block

                # Track the index for this loop
                self.loop_indices[block.uuid] = 0

                return loop_task_id

            loop_operations.append(create_progress_bar)

            def advance_progress_bar(variable_value: tuple[int | float, ...]) -> None:
                loop_task_id = task_ids[block.uuid]
                progress.update(
                    loop_task_id,
                    description=f"Looping over {label}: {variable_value[0] if len(variable_value) == 1 else variable_value}",
                )
                progress.advance(loop_task_id)

            def advance_loop_index() -> None:
                # Update the loop index
                self.loop_indices[block.uuid] += 1

            uuids = [variable.uuid for variable in self._variables_per_block[block]]
            values = [variable.values for variable in self._variables_per_block[block]]

            for current_values in zip(*values):
                for uuid, value in zip(uuids, current_values):
                    current_value_of_variable[uuid] = value

                loop_operations.append(lambda value=current_values: advance_progress_bar(value))  # type: ignore

                # Process elements within the loop
                loop_operations.extend(process_elements(block.elements))

                loop_operations.append(advance_loop_index)

            def remove_progress_bar():
                progress.remove_task(task_ids[block.uuid])
                del self.loop_indices[block.uuid]

            loop_operations.append(remove_progress_bar)

            return loop_operations

        def process_elements(elements: list[Block | Operation]) -> list[Callable]:
            """Process the elements in a block and store the corresponding operations."""
            elements_operations: list[Callable] = []

            for element in elements:
                if isinstance(element, GetParameter):
                    # Set current value of the variable to None
                    current_value_of_variable[element.variable.uuid] = None  # type: ignore[assignment]
                    # Append a lambda that will call the `platform.get_parameter` method and assign the returned value to the variable
                    elements_operations.append(
                        lambda operation=element: current_value_of_variable.update(
                            {
                                operation.variable.uuid: self.platform.get_parameter(
                                    alias=operation.alias,
                                    parameter=operation.parameter,
                                    channel_id=operation.channel_id,
                                    output_id=operation.output_id,
                                )
                            }
                        )
                    )
                if isinstance(element, SetCrosstalk):
                    elements_operations.append(
                        lambda operation=element: self.platform.set_crosstalk(crosstalk=operation.crosstalk)
                    )
                if isinstance(element, SetParameter):
                    # Append a lambda that will call the `platform.set_parameter` method
                    if isinstance(element.value, Variable):
                        if current_value_of_variable[element.value.uuid] is None:
                            # Variable has no value and it will get it from a `GetOperation` in the future. Thus, don't bind `value` in lambda.
                            elements_operations.append(
                                lambda operation=element: self.platform.set_parameter(
                                    alias=operation.alias,
                                    parameter=operation.parameter,
                                    value=current_value_of_variable[operation.value.uuid],
                                    channel_id=operation.channel_id,
                                    output_id=operation.output_id,
                                )
                            )
                        else:
                            # Variable has a value that was set from a loop. Thus, bind `value` in lambda with the current value of the variable.
                            elements_operations.append(
                                lambda operation=element, value=current_value_of_variable[
                                    element.value.uuid
                                ]: self.platform.set_parameter(
                                    alias=operation.alias,
                                    parameter=operation.parameter,
                                    value=value,
                                    channel_id=operation.channel_id,
                                    output_id=operation.output_id,
                                )
                            )
                    else:
                        # Value is not a variable. Treat it as a normal Python type.
                        elements_operations.append(
                            lambda operation=element: self.platform.set_parameter(
                                alias=operation.alias,
                                parameter=operation.parameter,
                                value=operation.value,
                                channel_id=operation.channel_id,
                                output_id=operation.output_id,
                            )
                        )

                if isinstance(element, ExecuteQProgram):
                    qprogram_index = self._qprogram_execution_indices[element]
                    if isinstance(element.qprogram, LambdaType):
                        signature = inspect.signature(element.qprogram)
                        call_parameters: dict[str, int | float] = {}
                        deferred_parameters: dict[str, UUID] = {}

                        # Iterate through parameters and separate the ones that have values and the ones that don't
                        for param in signature.parameters.values():
                            if isinstance(param.default, Variable):
                                variable_value = current_value_of_variable.get(param.default.uuid, None)
                                if variable_value is None:
                                    # The variable doesn't have a value yet; defer binding
                                    deferred_parameters[param.name] = param.default.uuid
                                    # Make sure key exists
                                    current_value_of_variable[param.default.uuid] = None  # type: ignore[assignment]
                                else:
                                    # The variable has a current value; bind it immediately
                                    call_parameters[param.name] = variable_value

                        # Bind the values for known variables, and retrieve deferred ones when the lambda is executed
                        elements_operations.append(
                            lambda operation=element, call_parameters=call_parameters, qprogram_index=qprogram_index: store_results(
                                self.platform.execute_qprogram(
                                    qprogram=operation.qprogram(
                                        **{
                                            **call_parameters,  # Bind the values that are known
                                            **{
                                                param_name: current_value_of_variable[uuid]
                                                for param_name, uuid in deferred_parameters.items()
                                            },  # Defer retrieving missing values
                                        }
                                    ),  # type: ignore
                                    bus_mapping=operation.bus_mapping,
                                    calibration=operation.calibration,
                                    debug=operation.debug,
                                ),
                                qprogram_index,
                            )
                        )
                    else:
                        # Append a lambda that will call the `platform.execute_qprogram` method
                        elements_operations.append(
                            lambda operation=element, qprogram_index=qprogram_index: store_results(
                                self.platform.execute_qprogram(
                                    qprogram=operation.qprogram,
                                    bus_mapping=operation.bus_mapping,
                                    calibration=operation.calibration,
                                    debug=operation.debug,
                                ),
                                qprogram_index,
                            )
                        )
                elif isinstance(element, Block):
                    # Recursively handle elements of the block
                    nested_operations = self._prepare_operations(element, progress)
                    elements_operations.extend(nested_operations)

            return elements_operations

        def store_results(qprogram_results: QProgramResults, qprogram_index: int):
            """Store the result in the correct location within the ExperimentResultsWriter."""
            # Determine the index based on current loop indices and store the results in the ExperimentResultsWriter
            for measurement_index, measurement_result in enumerate(qprogram_results.timeline):
                indices = (qprogram_index, measurement_index, *tuple(index for _, index in self.loop_indices.items()))
                self._results_writer[indices] = np.moveaxis(measurement_result.array, 0, -1)

        if isinstance(block, (Loop, ForLoop, Parallel)):
            # Handle loops
            operations.extend(handle_loop(block))
        else:
            # Handle generic blocks
            operations.extend(process_elements(block.elements))

        return operations

    def _execute_operations(self, operations: list[Callable], progress: Progress):
        """Run the stored operations in sequence, updating the progress bar."""
        main_task_id = progress.add_task("Executing experiment", total=len(operations))

        for operation in operations:
            # Execute the stored operation and update the main progress bar
            operation()
            progress.advance(main_task_id)

        progress.update(main_task_id, description="Executing experiment (done)")
        progress.refresh()  # Ensure the final state of the progress bar is rendered

    def _inclusive_range(self, start: int | float, stop: int | float, step: int | float) -> np.ndarray:
        # Check if all inputs are integers
        if all(isinstance(x, int) for x in [start, stop, step]):
            # Use numpy.arange for integer ranges
            return np.arange(start, stop + step, step)

        # Define the number of decimal places based on the precision of the step
        decimal_places = -int(np.floor(np.log10(step))) if step < 1 else 0

        # Calculate the number of steps
        num_steps = round((stop - start) / step) + 1

        # Use linspace and then round to avoid floating-point inaccuracies
        result = np.linspace(start, stop, num_steps)
        return np.around(result, decimals=decimal_places)

    def _get_variables_of_loop(self, block: Loop | ForLoop | Parallel) -> list[VariableInfo]:
        variables: dict[UUID, VariableInfo] = {}

        if isinstance(block, (ForLoop, Loop)):
            values = (
                self._inclusive_range(block.start, block.stop, block.step)
                if isinstance(block, ForLoop)
                else block.values
            )
            variable = VariableInfo(uuid=block.variable.uuid, label=block.variable.label, values=values)
            variables[block.variable.uuid] = variable
        else:
            for loop in block.loops:
                values = (
                    self._inclusive_range(loop.start, loop.stop, loop.step)
                    if isinstance(loop, ForLoop)
                    else loop.values
                )
                variable = VariableInfo(uuid=loop.variable.uuid, label=loop.variable.label, values=values)
                variables[loop.variable.uuid] = variable

        self._variables_per_block[block] = list(variables.values())

        # Update all_variables registry
        for variable in variables.values():
            if self._all_variables[variable.uuid]["label"] is None:
                self._all_variables[variable.uuid]["label"] = variable.label
            self._all_variables[variable.uuid]["values"][block.uuid] = variable.values

        return list(variables.values())

    def _create_results_path(self, executed_at: datetime):
        # Get base path and path format from platform

        base_path = self.platform.experiment_results_base_path
        path_format = self.platform.experiment_results_path_format

        # Format date and time for directory names
        date = executed_at.strftime("%Y%m%d")
        timestamp = executed_at.strftime("%H%M%S")
        label = self.experiment.label

        # Format the path based on the path's format
        path = path_format.format(date=date, time=timestamp, label=label)

        # Construct the full path
        path = os.path.join(base_path, path)

        # Ensure it is an absolute path
        path = os.path.abspath(path)

        # Create the directories if they don't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)

        return path

    def _measure_execution_time(self, execution_completed: threading.Event):
        """Measures the execution time while waiting for the experiment to finish."""
        # Start measuring execution time
        start_time = perf_counter()

        # Wait for the experiment to finish
        execution_completed.wait()

        # Stop measuring execution time
        end_time = perf_counter()

        # Return the execution time
        return end_time - start_time

    def execute(self) -> str:
        """
        Executes the experiment and streams the results in real-time.

        This method prepares the experiment by calculating the shape and values of the loops,
        creates callable operations, initializes an ExperimentResultsWriter for real-time result storage,
        and then runs the operations while updating a progress bar.

        Returns:
            str: The path to the file where the results are stored.
        """
        executed_at = datetime.now()

        # Create file path to store results
        results_path = self._create_results_path(executed_at=executed_at)

        # Prepare the results metadata
        self._prepare_metadata(executed_at=executed_at)

        # Create the ExperimentResultsWriter for storing results
        self._results_writer = ExperimentResultsWriter(
            path=results_path,
            metadata=self._metadata,
            db_metadata=self._db_metadata,
            db_manager=self.platform.db_manager,
            live_plot=self._live_plot,
            slurm_execution=self._slurm_execution,
            port_number=self._port_number,
        )

        # Event to signal that the execution has completed
        execution_completed = threading.Event()

        with ThreadPoolExecutor() as executor:
            # Start the _measure_execution_time in a separate thread
            execution_time_future = executor.submit(self._measure_execution_time, execution_completed)

            with self._results_writer:
                with Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(bar_width=None),
                    "[progress.percentage]{task.percentage:>3.1f}%",
                    TimeElapsedColumn(),
                ) as progress:
                    operations = self._prepare_operations(self.experiment.body, progress)
                    self._execute_operations(operations, progress)

                # Signal that the execution has completed
                execution_completed.set()

                # Retrieve the execution time from the Future
                execution_time = execution_time_future.result()

                # Now write the execution time to the results writer
                self._results_writer.execution_time = execution_time

        del self.loop_indices

        return self._results_writer.results_path
