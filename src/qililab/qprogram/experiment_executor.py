import os
import time
from typing import TYPE_CHECKING, Any, Callable

import numpy as np
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from qililab.qprogram.blocks import ForLoop, Loop
from qililab.qprogram.experiment import Experiment
from qililab.qprogram.operations import ExecuteQProgram, SetParameter
from qililab.result.qprogram.qprogram_results import QProgramResults
from qililab.result.stream_results import StreamArray, stream_results

if TYPE_CHECKING:
    from qililab.platform.platform import Platform


class ExperimentExecutor:
    """Manages the execution of a quantum experiment.

    The ExperimentExecutor is responsible for traversing the experiment's structure,
    managing loops and operations, and storing the results in a specified file.
    The results are saved in real-time using a StreamArray to ensure that data is not lost
    in case of interruptions during the experiment.
    """

    def __init__(self, platform: "Platform", experiment: Experiment, results_path: str):
        self.platform = platform  # Store the platform instance
        self.experiment = experiment
        self.task_ids: dict = {}
        self.stored_operations: list[Callable[[], Any]] = []
        self.results_path = results_path
        self.loop_indices: dict[str, int] = {}
        self.loop_values: dict[str, np.ndarray] = {}
        self.shape = ()
        self.stream_array: StreamArray

    def _prepare(self):
        """Prepares the loop values and result shape before execution."""
        self._traverse_and_prepare(self.experiment.body)
        self.shape = tuple(len(self.loop_values[loop_label]) for loop_label in self.loop_values) + (2,)

    def _traverse_and_prepare(self, block):
        """Traverses the blocks to gather loop information and determine result shape."""
        if isinstance(block, ForLoop):
            loop_values = self._inclusive_range(block.start, block.stop, block.step)
            loop_label = block.variable.label
            self.loop_values[loop_label] = loop_values
        elif isinstance(block, Loop):
            loop_values = block.values
            loop_label = block.variable.label
            self.loop_values[loop_label] = loop_values

        # Recursively traverse nested blocks or loops
        for element in getattr(block, "elements", []):
            if isinstance(element, (ForLoop, Loop)):
                self._traverse_and_prepare(element)
            # Handle ExecuteQProgram operations and traverse their loops
            if isinstance(element, ExecuteQProgram):
                self._traverse_qprogram(element.qprogram.body)

    def _traverse_qprogram(self, block):
        """Traverses a QProgram to gather loop information."""
        if isinstance(block, ForLoop):
            loop_values = self._inclusive_range(block.start, block.stop, block.step)
            loop_label = block.variable.label
            if loop_label not in self.loop_values:
                self.loop_values[loop_label] = loop_values
            else:
                # If the loop label already exists, ensure consistency
                assert np.array_equal(
                    self.loop_values[loop_label], loop_values
                ), f"Inconsistent loop values for {loop_label}"
        elif isinstance(block, Loop):
            loop_values = block.values
            loop_label = block.variable.label
            if loop_label not in self.loop_values:
                self.loop_values[loop_label] = loop_values
            else:
                # If the loop label already exists, ensure consistency
                assert np.array_equal(
                    self.loop_values[loop_label], loop_values
                ), f"Inconsistent loop values for {loop_label}"

        # Recursively handle nested blocks within the QProgram
        for element in getattr(block, "elements", []):
            if isinstance(element, (ForLoop, Loop)):
                self._traverse_qprogram(element)

    def _traverse_and_store(self, block, progress: Progress):
        """Traverse blocks, store generated Python functions, and return the stored operations."""
        stored_operations = []

        # Handle ForLoop or Loop blocks
        if isinstance(block, ForLoop) or isinstance(block, Loop):
            stored_operations.extend(self._handle_loop(block, progress))
        else:
            # Handle generic blocks
            stored_operations.extend(self._process_elements(block.elements, progress))

        return stored_operations

    def _handle_loop(self, block, progress: Progress) -> list[Callable]:
        """Common logic for handling ForLoop and Loop blocks."""
        stored_operations = []

        # Determine loop parameters based on the type of block
        loop_values: np.ndarray[int | float]
        if isinstance(block, ForLoop):
            loop_values = self._inclusive_range(block.start, block.stop, block.step)
        elif isinstance(block, Loop):
            loop_values = block.values  # Assuming `block.values` is a numpy array or similar iterable

        loop_label = block.variable.label

        # Create the progress bar for the loop
        def create_progress_bar():
            total_iterations = len(loop_values)
            loop_task_id = progress.add_task(f"Looping over {loop_label}", total=total_iterations)
            self.task_ids[block.uuid] = loop_task_id  # Store the task ID associated with this loop block

            # Track the index for this loop
            self.loop_indices[loop_label] = 0

            return loop_task_id

        stored_operations.append(create_progress_bar)

        def advance_progress_bar(variable_value: int | float) -> None:
            loop_task_id = self.task_ids[block.uuid]
            progress.update(loop_task_id, description=f"Looping over {loop_label}: {variable_value}")
            progress.advance(loop_task_id)

            # Update the loop index
            self.loop_indices[loop_label] += 1

        for value in loop_values:
            stored_operations.append(lambda value=value: advance_progress_bar(value))  # type: ignore

            # Process elements within the loop
            stored_operations.extend(self._process_elements(block.elements, progress))

        def remove_progress_bar():
            progress.remove_task(self.task_ids[block.uuid])

        stored_operations.append(remove_progress_bar)

        return stored_operations

    def _process_elements(self, elements, progress: Progress) -> list[Callable]:
        """Process the elements in a block and store the corresponding operations."""
        stored_operations = []

        for element in elements:
            if isinstance(element, SetParameter):
                stored_operations.append(
                    lambda op=element: self.platform.set_parameter(op.alias, op.parameter, op.value)
                )

            elif isinstance(element, ExecuteQProgram):
                stored_operations.append(
                    lambda op=element: self._store_result(self.platform.execute_qprogram(op.qprogram))
                )

            elif isinstance(element, (ForLoop, Loop)):
                nested_operations = self._traverse_and_store(element, progress)
                stored_operations.extend(nested_operations)

        return stored_operations

    def _store_result(self, result: QProgramResults):
        """Store the result in the correct location within the StreamArray."""
        # Determine the index in the StreamArray based on current loop indices
        indices = tuple(self.loop_indices[loop_label] - 1 for loop_label in self.loop_indices)
        self.stream_array[indices] = next(iter(result.results.values()))[0].array.T

    def _run_stored_operations(self, progress: Progress):
        """Run the stored operations in sequence, updating the progress bar."""
        main_task_id = progress.add_task("Executing experiment", total=len(self.stored_operations))

        for operation in self.stored_operations:
            operation()  # Execute the stored operation
            progress.advance(main_task_id)  # Manually update the progress for each operation

        progress.update(main_task_id, description="Executing experiment (done)")
        progress.refresh()  # Ensure the final state of the progress bar is rendered

    def _inclusive_range(self, start: int | float, stop: int | float, step: int | float) -> np.ndarray:
        # Check if all inputs are integers
        if all(isinstance(x, int) for x in [start, stop, step]):
            # Use numpy.arange for integer ranges
            return np.arange(start, stop + step, step)
        else:
            # Define the number of decimal places based on the precision of the step
            decimal_places = -int(np.floor(np.log10(step))) if step < 1 else 0

            # Calculate the number of steps
            num_steps = int(round((stop - start) / step)) + 1

            # Use linspace and then round to avoid floating-point inaccuracies
            result = np.linspace(start, stop, num_steps)
            return np.around(result, decimals=decimal_places)

    def _create_directories(self, source):
        t = time.localtime()
        date = time.strftime("%Y%m%d", t)
        timestamp = time.strftime("%H%M%S")

        folder = f"{source}{date}/{timestamp}/"
        if not os.path.isdir(folder):
            os.makedirs(folder)

        return folder

    def execute(self) -> list[Any]:
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
        path = self._create_directories(self.results_path) + "data.h5"

        # Prepare the experiment, calculate shape and loop values
        self._prepare()

        # Create the StreamArray for storing results
        self.stream_array = stream_results(shape=self.shape, loops=self.loop_values, path=path)

        with self.stream_array:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                TimeElapsedColumn(),
            ) as progress:
                self.stored_operations = self._traverse_and_store(self.experiment.body, progress)
                self._run_stored_operations(progress)

        return path
