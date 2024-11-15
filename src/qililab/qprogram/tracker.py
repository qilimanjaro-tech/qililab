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
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable

from qililab.qprogram.experiment import Experiment
from qililab.qprogram.tracker_writer import BlockMetadata, TrackerMetadata, TrackerWriter
from qililab.result.experiment_results import ExperimentResults
from qililab.result.experiment_results_writer import VariableMetadata
from qililab.yaml import yaml


@yaml.register_class
class Tracker:
    """This class contains the logic and tools needed to follow a feature while being completely generic"""

    def __init__(
        self,
    ) -> None:
        """_summary_

        Args:
            find_relevant_point (function): takes the data from measure as input and finds the relevant point
            predict_next_point (function): takes all the previously found points of interest and predicts the next
            update_window (function): with the predicted point as input, updates the window for the measurement
        """

        self.alias_list: list[str] = []
        self.measure_dict: dict[str, Experiment] = {}
        self.find_relevant_point_dict: dict[str, Callable] = {}
        self.update_window_dict: dict[str, Callable] = {}

        self.real_path: dict[str, list] = {}
        self.guessed_path: dict[str, list] = {}
        self.windows: dict[str, list] = {}
        self.total_data: dict[str, list] = {}
        self.experiment_dims: dict[str, list] = {}

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

    def build_measure_block(
        self,
        alias: str,
        measure: Callable,
        find_relevant_point: Callable,
        update_window: Callable,
    ):
        self.alias_list.append(alias)
        self.measure_dict[alias] = measure
        self.find_relevant_point_dict[alias] = find_relevant_point
        self.update_window_dict[alias] = update_window

        self.real_path[alias] = []
        self.guessed_path[alias] = []
        self.windows[alias] = []
        self.total_data[alias] = []
        self.experiment_dims[alias] = []

    def run_tracker(
        self,
        parameter_alias: str,
        set_parameter: Callable,
        values: list,
        initial_guess: float,
        tracker_path: str,
        # live_plot: bool = False, #TODO: add live plotting
    ) -> None:
        """Runs the

        Args:
            parameter (Parameter): parameter to be changed
            values (list): values for the parameter
            guess (float): first starting point for the window
        """
        # if self.alias_list empty:
        #     raise Error
        guess = initial_guess
        executed_at = datetime.now()

        experiments = BlockMetadata(
            alias=self.alias,
            real_path=self.real_path,
            guessed_path=self.guessed_path,
            windows=self.windows,
            total_data=self.total_data,
            experiment_dims=self.experiment_dims,
        )
        metadata = TrackerMetadata(
            executed_at=executed_at,
            execution_time=0.0,
            values=VariableMetadata(label=parameter_alias, values=values),
            experiments=experiments,
        )

        tracker_writer = TrackerWriter(tracker_path, metadata)

        execution_completed = threading.Event()

        with ThreadPoolExecutor() as executor:
            # Start the _measure_execution_time in a separate thread
            execution_time_future = executor.submit(self._measure_execution_time, execution_completed)

            for value in values:
                # Set the parameter
                set_parameter(value)

                for operation in self.alias_list:
                    # Update the window
                    window, predicted_guess = self.update_window_dict[operation](guess)
                    self.windows[operation].append(window)
                    self.guessed_path[operation].append(predicted_guess)

                    # Do the experiment
                    data, dims = self.measure_dict[operation](
                        window, predicted_guess, tracker_writer.experiment_path[operation][value]
                    )
                    self.total_data[operation].append(data)
                    self.experiment_dims[operation].append(dims)

                    # Measure the point of interest
                    guess = self.find_relevant_point_dict[operation](data, window)
                    self.real_path[operation].append(guess)

                    tracker_writer.set(
                        alias=operation,
                        window=self.windows[operation],
                        guess_path=self.guessed_path[operation],
                        data=self.total_data[operation],
                        real_path=self.real_path[operation],
                    )

            # Signal that the execution has completed
            execution_completed.set()
            # Retrieve the execution time from the Future
            execution_time = execution_time_future.result()
            # Now write the execution time to the results writer
            with tracker_writer:
                tracker_writer.execution_time = execution_time

        return tracker_writer.path


# ADD MODIFIABLE VARIABLES INSIDE EXPERIMENTS TO SAVE THEM LATER IN THE SAME PLACE, VARIABLES THAT CHANGE INSIDE THE LOOP
