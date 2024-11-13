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
        parameter_alias:str,
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

        guess = initial_guess

        for value in values:
            # Set the parameter
            set_parameter(value)
            
            for operation in self.alias_list:
                # Update the window
                window, predicted_guess = self.update_window_dict[operation](guess)
                self.windows[operation].append(window)
                self.guessed_path[operation].append(predicted_guess)

                # Do the experiment
                data, dims = self.measure_dict[operation](window, predicted_guess, tracker_path)
                self.total_data[operation].append(data)
                self.experiment_dims[operation].append(dims)

                # Measure the point of interest
                guess = self.find_relevant_point_dict[operation](data, window)
                self.real_path[operation].append(guess)
        return


# ASK VYRON HOW TO SAVE THE REST OF THE DATA INSIDE EXPERIMENTS, MODIFY EXPERIMENTS IF NECESSARY
# ADD MODIFYIABLE VARIABLES INSIDE EXPERIMENTS TO SAVE THEM LATER IN THE SAME PLACE, VARIABLES THAT CHANGE INSIDE THE LOOP
