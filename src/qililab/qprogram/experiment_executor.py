# mypy: disable-error-code="union-attr, arg-type"
import os
from collections import defaultdict, namedtuple
from copy import deepcopy
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable
from uuid import UUID

import numpy as np
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from qililab.qprogram.blocks import Average, Block, ForLoop, Loop, Parallel
from qililab.qprogram.experiment import Experiment
from qililab.qprogram.operations import ExecuteQProgram, Measure, Operation, SetParameter
from qililab.qprogram.qprogram import QProgram
from qililab.qprogram.variable import Variable
from qililab.result.experiment_results_writer import (
    ExperimentMetadata,
    ExperimentResultsWriter,
    MeasurementMetadata,
    QProgramMetadata,
)
from qililab.result.qprogram.qprogram_results import QProgramResults
from qililab.utils.serialization import serialize

if TYPE_CHECKING:
    from qililab.platform.platform import Platform

VariableInfo = namedtuple("VariableInfo", ["uuid", "label", "values"])


class ExperimentExecutor:  # pylint: disable=too-few-public-methods
    """Manages the execution of a quantum experiment.

    The ExperimentExecutor is responsible for traversing the experiment's structure,
    managing loops and operations, and storing the results in a specified file.
    The results are saved in real-time using a StreamArray to ensure that data is not lost
    in case of interruptions during the experiment.
    """

    def __init__(self, platform: "Platform", experiment: Experiment, results_path: str):
        self.platform = platform
        self.experiment = experiment
        self.results_path = results_path
        self.task_ids: dict = {}
        self.stored_operations: list[Callable[[], Any]] = []

        self.all_variables: dict = defaultdict(lambda: {"label": None, "values": {}})
        self.variables_per_block: dict[UUID, list] = {}
        self.current_block_of_variable: dict[UUID, UUID] = {}
        self.current_value_of_variable: dict[UUID, int | float] = {}

        self.variable_in_loop_values: dict[str, dict[UUID, np.ndarray]] = defaultdict(dict)
        self.loop_indices: dict[UUID, int] = {}
        self.qprogram_execution_indices: dict[UUID, int] = {}

        self.experiment_variables_stack: list = []
        self.qprogram_variables_stack: list = []
        self.qprogram_index = 0
        self.measurement_index = 0
        self.shots = 1
        self.metadata: ExperimentMetadata = ExperimentMetadata(
            yaml=None, executed_at=None, execution_time=None, qprograms={}
        )
        self.results_writer: ExperimentResultsWriter

    def _prepare(self):
        """Prepares the loop values and result shape before execution."""

        def traverse_experiment(block: Block):
            """Traverses the blocks to gather loop information and determine result shape."""
            if isinstance(block, (Loop, ForLoop, Parallel)):
                variables = self.get_variables_of_loop(block)

                self.experiment_variables_stack.append(variables)

            # Recursively traverse nested blocks or loops
            for element in block.elements:
                if isinstance(element, Block):
                    traverse_experiment(element)
                # Handle ExecuteQProgram operations and traverse their loops
                if isinstance(element, ExecuteQProgram):
                    traverse_qprogram(element.qprogram.body)
                    self.qprogram_execution_indices[element.uuid] = self.qprogram_index
                    self.measurement_index = 0
                    self.qprogram_index += 1

            if isinstance(block, (Loop, ForLoop, Parallel)):
                del self.experiment_variables_stack[-1]

        def traverse_qprogram(block: Block):
            """Traverses a QProgram to gather loop information."""
            if isinstance(block, (Loop, ForLoop, Parallel)):
                variables = self.get_variables_of_loop(block)

                self.qprogram_variables_stack.append(variables)
            if isinstance(block, Average):
                self.shots = block.shots

            # Recursively handle nested blocks within the QProgram
            for element in block.elements:
                if isinstance(element, Block):
                    traverse_qprogram(element)
                if isinstance(element, Measure):
                    finalize_measurement_structure()

            if isinstance(block, (Loop, ForLoop, Parallel)):
                del self.qprogram_variables_stack[-1]
            if isinstance(block, Average):
                self.shots = 1

        def finalize_measurement_structure():
            """Finalize the structure of a measurement when a Measure operation is encountered."""
            qprogram_name = f"QProgram_{self.qprogram_index}"
            measurement_name = f"Measurement_{self.measurement_index}"

            # Ensure QProgram exists in the structure
            if qprogram_name not in self.metadata["qprograms"]:
                self.metadata["qprograms"][qprogram_name] = QProgramMetadata(
                    variables=[variable for sublist in self.experiment_variables_stack for variable in sublist],
                    dims=[[variable["label"] for variable in sublist] for sublist in self.experiment_variables_stack],
                    measurements={},
                )

            # Add QProgram loops and the measurement
            self.metadata["qprograms"][qprogram_name]["measurements"][measurement_name] = MeasurementMetadata(
                variables=[variable for sublist in self.qprogram_variables_stack for variable in sublist],
                dims=[[variable["label"] for variable in sublist] for sublist in self.qprogram_variables_stack],
                shape=tuple(
                    len(sublist[0]["values"])
                    for sublist in (self.experiment_variables_stack + self.qprogram_variables_stack)
                )
                + (2,),
                shots=self.shots,
            )

            # Increase index of measurements
            self.measurement_index += 1

        traverse_experiment(self.experiment.body)
        self.all_variables = dict(self.all_variables)

    def _traverse_and_store(self, block: Block, progress: Progress):
        """Traverse blocks, store generated Python functions, and return the stored operations."""
        stored_operations = []

        if isinstance(block, (Loop, ForLoop, Parallel)):
            # Handle loops
            stored_operations.extend(self._handle_loop(block, progress))
        else:
            # Handle generic blocks
            stored_operations.extend(self._process_elements(block.elements, progress))

        return stored_operations

    def _handle_loop(self, block: ForLoop | Loop | Parallel, progress: Progress) -> list[Callable]:
        """Common logic for handling ForLoop and Loop blocks."""
        stored_operations = []

        # Determine loop parameters based on the type of block
        label = ",".join([variable["label"] for variable in self.variables_per_block[block.uuid]])
        shape = self.variables_per_block[block.uuid][0]["values"].shape[-1]

        for variable in self.variables_per_block[block.uuid]:
            self.current_block_of_variable[variable["uuid"]] = block.uuid

        # Create the progress bar for the loop
        def create_progress_bar():
            total_iterations = shape
            loop_task_id = progress.add_task(f"Looping over {label}", total=total_iterations)
            self.task_ids[block.uuid] = loop_task_id  # Store the task ID associated with this loop block

            # Track the index for this loop
            self.loop_indices[block.uuid] = 0

            return loop_task_id

        stored_operations.append(create_progress_bar)

        def advance_progress_bar(variable_value: tuple[int | float, ...]) -> None:
            loop_task_id = self.task_ids[block.uuid]
            progress.update(
                loop_task_id,
                description=f"Looping over {label}: {variable_value[0] if len(variable_value) == 1 else variable_value}",
            )
            progress.advance(loop_task_id)

        def advance_loop_index() -> None:
            # Update the loop index
            self.loop_indices[block.uuid] += 1

        uuids = [variable["uuid"] for variable in self.variables_per_block[block.uuid]]
        values = [variable["values"] for variable in self.variables_per_block[block.uuid]]

        for current_values in zip(*values):
            for uuid, value in zip(uuids, current_values):
                self.current_value_of_variable[uuid] = value

            stored_operations.append(lambda value=current_values: advance_progress_bar(value))  # type: ignore

            # Process elements within the loop
            stored_operations.extend(self._process_elements(block.elements, progress))

            stored_operations.append(advance_loop_index)

        def remove_progress_bar():
            progress.remove_task(self.task_ids[block.uuid])
            del self.loop_indices[block.uuid]

        stored_operations.append(remove_progress_bar)

        return stored_operations

    def _process_elements(self, elements: list[Block | Operation], progress: Progress) -> list[Callable]:
        """Process the elements in a block and store the corresponding operations."""
        stored_operations = []

        for element in elements:
            if isinstance(element, SetParameter):
                # Append a lambda that will call the `platform.set_parameter` method
                stored_operations.append(
                    lambda alias=element.alias, parameter=element.parameter, value=(
                        self.current_value_of_variable[element.value.uuid]
                        if isinstance(element.value, Variable)
                        else element.value
                    ): self.platform.set_parameter(alias=alias, parameter=parameter, value=value)
                )

            if isinstance(element, ExecuteQProgram):
                # Append a lambda that will call the `platform.execute_qprogram` method
                stored_operations.append(
                    lambda op=element, qprogram_index=self.qprogram_execution_indices[element.uuid]: self._store_result(  # type: ignore[misc]
                        self.platform.execute_qprogram(
                            qprogram=op.qprogram, bus_mapping=op.bus_mapping, calibration=op.calibration, debug=op.debug
                        ),
                        qprogram_index,
                    )
                )
            elif isinstance(element, Block):
                # Recursively handle elements of the block
                nested_operations = self._traverse_and_store(element, progress)
                stored_operations.extend(nested_operations)

        return stored_operations

    def _store_result(self, result: QProgramResults, qprogram_index: int):
        """Store the result in the correct location within the StreamArray."""
        # Determine the index in the StreamArray based on current loop indices
        for measurement_index, results in enumerate(next(iter(result.results.values()))):
            loop_indices = tuple(index - 1 for _, index in self.loop_indices.items())
            indices = tuple([qprogram_index, measurement_index]) + loop_indices
            # Store the results in the StreamArray
            self.results_writer[indices] = results.array.T  # type: ignore

    def _run_stored_operations(self, progress: Progress):
        """Run the stored operations in sequence, updating the progress bar."""
        main_task_id = progress.add_task("Executing experiment", total=len(self.stored_operations))

        for operation in self.stored_operations:
            # Execute the stored operation and update the main progress bar
            operation()
            progress.advance(main_task_id)

        progress.update(main_task_id, description="Executing experiment (done)")
        progress.refresh()  # Ensure the final state of the progress bar is rendered
        return progress.tasks[main_task_id].elapsed

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

    def get_variables_of_loop(self, block: Loop | ForLoop | Parallel):
        # Get variable information of the loop
        if isinstance(block, (ForLoop, Loop)):
            variables = {
                block.variable.uuid: {
                    "label": block.variable.label,
                    "values": {
                        block.uuid: self._inclusive_range(block.start, block.stop, block.step)
                        if isinstance(block, ForLoop)
                        else block.values
                    },
                }
            }
        else:
            variables = {
                loop.variable.uuid: {
                    "label": loop.variable.label,
                    "values": {
                        block.uuid: self._inclusive_range(loop.start, loop.stop, loop.step)
                        if isinstance(loop, ForLoop)
                        else loop.values
                    },
                }
                for loop in block.loops
            }

        self.variables_per_block[block.uuid] = []

        # Update all_variables registry
        for outer_key, outer_value in variables.items():
            self.variables_per_block[block.uuid].append(
                {"uuid": outer_key, "label": outer_value["label"], "values": next(iter(outer_value["values"].values()))}
            )

            # Set label (assumes label is consistent for the same outer_key)
            if self.all_variables[outer_key]["label"] is None:
                self.all_variables[outer_key]["label"] = outer_value["label"]

            # Merge the "values" dictionaries
            self.all_variables[outer_key]["values"].update(outer_value["values"])

        return [
            {"label": variable["label"], "values": next(iter(variable["values"].values()))}
            for variable in variables.values()
        ]

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

        This method prepares the experiment by calculating the shape and values
        of the loops, initializes the StreamArray for real-time result storage,
        and then runs the stored operations while updating a progress bar.
        The results are saved in a file located at the specified results path.

        Returns:
            str: The path to the file where the results are stored.
        """
        # Create file path to store results
        path = self._create_results_path(self.results_path, "data.h5")

        # Prepare the experiment, calculate shape and loop values
        self._prepare()

        # Update metadata
        self.metadata["yaml"] = serialize(self.experiment)
        self.metadata["executed_at"] = str(datetime.now())

        # Create the ExperimentResultsWriter for storing results
        self.results_writer = ExperimentResultsWriter(metadata=self.metadata, path=path)
        with self.results_writer:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                TimeElapsedColumn(),
            ) as progress:
                self.stored_operations = self._traverse_and_store(self.experiment.body, progress)
                self.results_writer.execution_time = self._run_stored_operations(progress)

        return path
