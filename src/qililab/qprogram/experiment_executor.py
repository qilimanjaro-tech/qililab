import os
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

import numpy as np
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from qililab.qprogram.blocks import Block, ForLoop, Loop
from qililab.qprogram.experiment import Experiment
from qililab.qprogram.operations import ExecuteQProgram, Operation, SetParameter
from qililab.qprogram.variable import Variable
from qililab.result.qprogram.qprogram_results import QProgramResults
from qililab.result.stream_results import StreamArray, stream_results

if TYPE_CHECKING:
    from qililab.platform.platform import Platform


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
        self.loop_indices: dict[str, int] = {}
        self.loop_values: dict[str, np.ndarray] = {}
        self.shape = ()
        self.stream_array: StreamArray

    def _prepare(self):
        """Prepares the loop values and result shape before execution."""
        self._traverse_and_prepare(self.experiment.body)
        self.shape = tuple(len(values) for _, values in self.loop_values.items()) + (2,)

    def _traverse_and_prepare(self, block: Block):
        """Traverses the blocks to gather loop information and determine result shape."""
        if isinstance(block, (Loop, ForLoop)):
            loop_values = (
                self._inclusive_range(block.start, block.stop, block.step)
                if isinstance(block, ForLoop)
                else block.values
            )
            loop_label = block.variable.label
            self.loop_values[loop_label] = loop_values

        # Recursively traverse nested blocks or loops
        for element in block.elements:
            if isinstance(element, (ForLoop, Loop)):
                self._traverse_and_prepare(element)
            # Handle ExecuteQProgram operations and traverse their loops
            if isinstance(element, ExecuteQProgram):
                self._traverse_qprogram(element.qprogram.body)

    def _traverse_qprogram(self, block: Block):
        """Traverses a QProgram to gather loop information."""
        if isinstance(block, ForLoop):
            loop_values = self._inclusive_range(block.start, block.stop, block.step)
            loop_label = block.variable.label
            self.loop_values[loop_label] = loop_values
        elif isinstance(block, Loop):
            loop_values = block.values
            loop_label = block.variable.label
            self.loop_values[loop_label] = loop_values

        # Recursively handle nested blocks within the QProgram
        for element in block.elements:
            if isinstance(element, Block):
                self._traverse_qprogram(element)

    def _traverse_and_store(self, block: Block, progress: Progress):
        """Traverse blocks, store generated Python functions, and return the stored operations."""
        stored_operations = []

        if isinstance(block, (Loop, ForLoop)):
            # Handle loops
            stored_operations.extend(self._handle_loop(block, progress))
        else:
            # Handle generic blocks
            stored_operations.extend(self._process_elements(block.elements, progress))

        return stored_operations

    def _handle_loop(self, block: ForLoop | Loop, progress: Progress) -> list[Callable]:
        """Common logic for handling ForLoop and Loop blocks."""
        stored_operations = []

        # Determine loop parameters based on the type of block
        loop_values: np.ndarray
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

        def advance_loop_index() -> None:
            # Update the loop index
            self.loop_indices[loop_label] += 1

        for value in loop_values:
            stored_operations.append(lambda value=value: advance_progress_bar(value))  # type: ignore

            # Process elements within the loop
            stored_operations.extend(self._process_elements(block.elements, progress))

            stored_operations.append(advance_loop_index)

        def remove_progress_bar():
            progress.remove_task(self.task_ids[block.uuid])

        stored_operations.append(remove_progress_bar)

        return stored_operations

    def _process_elements(self, elements: list[Block | Operation], progress: Progress) -> list[Callable]:
        """Process the elements in a block and store the corresponding operations."""
        stored_operations = []

        for element in elements:
            if isinstance(element, SetParameter):
                # Append a lambda that will call the `platform.set_parameter` method
                stored_operations.append(
                    lambda op=element: self.platform.set_parameter(
                        alias=op.alias,
                        parameter=op.parameter,
                        value=self.loop_values[op.value.label][self.loop_indices[op.value.label]],
                    )
                    if isinstance(op.value, Variable)
                    else self.platform.set_parameter(alias=op.alias, parameter=op.parameter, value=op.value)
                )
            elif isinstance(element, ExecuteQProgram):
                # Append a lambda that will call the `platform.execute_qprogram` method
                stored_operations.append(
                    lambda op=element: self._store_result(
                        self.platform.execute_qprogram(
                            qprogram=op.qprogram, bus_mapping=op.bus_mapping, calibration=op.calibration, debug=op.debug
                        )
                    )
                )
            elif isinstance(element, Block):
                # Recursively handle elements of the block
                nested_operations = self._traverse_and_store(element, progress)
                stored_operations.extend(nested_operations)

        return stored_operations

    def _store_result(self, result: QProgramResults):
        """Store the result in the correct location within the StreamArray."""
        # Determine the index in the StreamArray based on current loop indices
        indices = tuple(index - 1 for _, index in self.loop_indices.items())
        # Store the results in the StreamArray
        self.stream_array[indices] = next(iter(result.results.values()))[0].array.T  # type: ignore

    def _run_stored_operations(self, progress: Progress):
        """Run the stored operations in sequence, updating the progress bar."""
        main_task_id = progress.add_task("Executing experiment", total=len(self.stored_operations))

        for operation in self.stored_operations:
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
