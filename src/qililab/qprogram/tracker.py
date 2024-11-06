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
from typing import Callable

from qililab.platform.platform import Platform
from qililab.qprogram.experiment import Experiment
from qililab.result.experiment_results import ExperimentResults
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
        platform: Platform,
        set_parameter: Callable,
        values: list,
        initial_guess: float,
        data_path: str,
        # plot: bool = False, #TODO: add live plotting
    ) -> None:
        """Runs the

        Args:
            parameter (Parameter): parameter to be changed
            values (list): values for the parameter
            guess (float): first starting point for the window
        """

        guess = initial_guess

        for value in values:
            for operation in self.alias_list:

                # Set the parameter
                set_parameter(value)

                # Update the window
                window, predicted_point = self.update_window_dict[operation](guess)
                self.windows[operation].append(window)
                self.guessed_path[operation].append(predicted_point)

                # Do the experiment
                experiment = self.measure_dict[operation](self.windows)
                with platform.session():
                    results_path = platform.execute_experiment(experiment, data_path)
                with ExperimentResults(results_path) as results:
                    data, dims = results.get()
                self.total_data[operation].append(data)
                self.experiment_dims[operation].append(dims)

                # Measure the point of interest
                guess = self.find_relevant_point_dict[operation](data)
                self.windows[operation].append(window)
        return


# ASK VYRON ABOUT SESSION AND HOW TO EXECUTE EXPERIMENT WITHOUT IT
# ASK VYRON HOW TO SAVE THE REST OF THE DATA INSIDE EXPERIMENTS, MODIFY EXPERIMENTS IF NECESSARY
# ADD MODIFIABLE VARIABLES INSIDE EXPERIMENTS TO SAVE THEM LATER IN THE SAME PLACE, VARIABLES THAT CHANGE INSIDE THE LOOP
# Flag timeout QM
