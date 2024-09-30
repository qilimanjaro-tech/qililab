# mypy: disable-error-code="union-attr, arg-type"
import inspect
import os
from collections import defaultdict
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
from qililab.qprogram.operations import ExecuteQProgram, Measure, Operation, SetParameter
from qililab.qprogram.variable import Variable
from qililab.result.experiment_results_writer import (
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


# pylint: disable=too-few-public-methods
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

    Example:
        .. code-block::

            from qililab.data_management import build_platform
            from qililab.qprogram import Experiment
            from qililab.executor import ExperimentExecutor

            # Initialize the platform
            platform = build_platform(runcard="path/to/runcard.yml")

            # Define your experiment
            experiment = Experiment()
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

    def __init__(self, platform: "Platform", experiment: Experiment, base_data_path: str):
        self.platform = platform
        self.experiment = experiment
        self.base_data_path = base_data_path

        # Registry of all variables used in the experiment with their labels and values
        self._all_variables: dict = defaultdict(lambda: {"label": None, "values": {}})

        # Mapping from each block's UUID to the list of variables associated with that block
        self._variables_per_block: dict[UUID, list[VariableInfo]] = {}

        # Mapping from each ExecuteQProgram operation's UUID to its execution index (order of execution)
        self._qprogram_execution_indices: dict[UUID, int] = {}

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
        self._metadata: ExperimentMetadata = ExperimentMetadata(qprograms={})

        # ExperimentResultsWriter object responsible for saving experiment results to file in real-time.
        self._results_writer: ExperimentResultsWriter

    def _prepare_metadata(self):
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
                    self._qprogram_execution_indices[element.uuid] = self._qprogram_index
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
                shape=tuple(
                    len(sublist[0].values)
                    for sublist in (self._experiment_variables_stack + self._qprogram_variables_stack)
                )
                + (2,),
                shots=self._shots,
            )

            # Increase index of measurements
            self._measurement_index += 1

        traverse_experiment(self.experiment.body)
        self._all_variables = dict(self._all_variables)

    def _prepare_operations(self, block: Block, progress: Progress):
        """Traverse blocks, store generated Python functions, and return the stored operations."""

        # A mapping from block UUID to the associated Progress TaskID
        task_ids: dict[UUID, TaskID] = {}

        # A list of operations to execute
        operations: list[Callable] = []

        # A mapping from block UUID to the index of the current value of its variable
        loop_indices: dict[UUID, int] = {}

        # A mapping from variable UUID to current value of the variable
        current_value_of_variable: dict[UUID, int | float] = {}

        def handle_loop(block: ForLoop | Loop | Parallel) -> list[Callable]:
            """Common logic for handling ForLoop and Loop blocks."""
            loop_operations: list[Callable] = []

            # Determine loop parameters based on the type of block
            label = ",".join([variable.label for variable in self._variables_per_block[block.uuid]])
            shape = self._variables_per_block[block.uuid][0].values.shape[-1]

            # Create the progress bar for the loop
            def create_progress_bar():
                total_iterations = shape
                loop_task_id = progress.add_task(f"Looping over {label}", total=total_iterations)
                task_ids[block.uuid] = loop_task_id  # Store the task ID associated with this loop block

                # Track the index for this loop
                loop_indices[block.uuid] = 0

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
                loop_indices[block.uuid] += 1

            uuids = [variable.uuid for variable in self._variables_per_block[block.uuid]]
            values = [variable.values for variable in self._variables_per_block[block.uuid]]

            for current_values in zip(*values):
                for uuid, value in zip(uuids, current_values):
                    current_value_of_variable[uuid] = value

                loop_operations.append(lambda value=current_values: advance_progress_bar(value))  # type: ignore

                # Process elements within the loop
                loop_operations.extend(process_elements(block.elements))

                loop_operations.append(advance_loop_index)

            def remove_progress_bar():
                progress.remove_task(task_ids[block.uuid])
                del loop_indices[block.uuid]

            loop_operations.append(remove_progress_bar)

            return loop_operations

        def process_elements(elements: list[Block | Operation]) -> list[Callable]:
            """Process the elements in a block and store the corresponding operations."""
            elements_operations: list[Callable] = []

            for element in elements:
                if isinstance(element, SetParameter):
                    # Append a lambda that will call the `platform.set_parameter` method
                    elements_operations.append(
                        lambda alias=element.alias, parameter=element.parameter, value=(
                            current_value_of_variable[element.value.uuid]
                            if isinstance(element.value, Variable)
                            else element.value
                        ): self.platform.set_parameter(alias=alias, parameter=parameter, value=value)
                    )

                if isinstance(element, ExecuteQProgram):
                    if isinstance(element.qprogram, LambdaType):
                        signature = inspect.signature(element.qprogram)
                        call_parameters = {
                            param.name: current_value_of_variable[param.default.uuid]
                            for param in signature.parameters.values()
                            if isinstance(param.default, Variable)
                        }
                        qprogram = element.qprogram(**call_parameters)
                        elements_operations.append(
                            lambda operation=element, qprogram=qprogram, qprogram_index=self._qprogram_execution_indices[element.uuid]: store_results(  # type: ignore[misc]
                                self.platform.execute_qprogram(
                                    qprogram=qprogram,
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
                            lambda operation=element, qprogram_index=self._qprogram_execution_indices[element.uuid]: store_results(  # type: ignore[misc]
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
            # Determine the index in the ExperimentResultsWriter based on current loop indices
            for measurement_index, measurement_result in enumerate(qprogram_results.timeline):
                indices = (qprogram_index, measurement_index) + tuple(index for _, index in loop_indices.items())
                # Store the results in the ExperimentResultsWriter
                self._results_writer[indices] = measurement_result.array.T  # type: ignore

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
        num_steps = int(round((stop - start) / step)) + 1

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

        self._variables_per_block[block.uuid] = list(variables.values())

        # Update all_variables registry
        for variable in variables.values():
            if self._all_variables[variable.uuid]["label"] is None:
                self._all_variables[variable.uuid]["label"] = variable.label
            self._all_variables[variable.uuid]["values"][block.uuid] = variable.values

        return list(variables.values())

    def _create_results_path(self, source: str, file: str):
        # Get the current date and time
        now = datetime.now()

        # Format date and time for directory names
        date = now.strftime("%Y%m%d")
        timestamp = now.strftime("%H%M%S")

        # Construct the directory path
        folder = os.path.join(source, date, timestamp)

        # Create the directories if they don't exist
        os.makedirs(folder, exist_ok=True)

        path = os.path.join(folder, file)

        return path

    def execute(self) -> str:
        """
        Executes the experiment and streams the results in real-time.

        This method prepares the experiment by calculating the shape and values of the loops,
        creates callable operations, initializes an ExperimentResultsWriter for real-time result storage,
        and then runs the operations while updating a progress bar.

        Returns:
            str: The path to the file where the results are stored.
        """
        # Create file path to store results
        path = self._create_results_path(self.base_data_path, "data.h5")

        # Prepare the results metadata
        self._prepare_metadata()

        # Update metadata
        self._metadata["platform"] = serialize(self.platform.to_dict())
        self._metadata["experiment"] = serialize(self.experiment)
        self._metadata["executed_at"] = datetime.now()

        # Create the ExperimentResultsWriter for storing results
        self._results_writer = ExperimentResultsWriter(path=path, metadata=self._metadata)
        with self._results_writer:
            start_time = perf_counter()

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                TimeElapsedColumn(),
            ) as progress:
                operations = self._prepare_operations(self.experiment.body, progress)
                self._execute_operations(operations, progress)

            self._results_writer.execution_time = perf_counter() - start_time

        return path
