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
import numpy as np

from qililab.qprogram.calibration import Calibration
from qililab.qprogram.qprogram import QProgram
from qililab.qprogram.structured_program import StructuredProgram
from qililab.qprogram.experiment import Experiment
from qililab.typings.enums import Parameter
from qililab.yaml import yaml

import qcodes as qc
from IPython.display import display, clear_output
import matplotlib.pyplot as plt

from queue import Empty, Queue
from threading import Thread


@yaml.register_class
class Tracker:
    """ This class contains the logic and tools needed to follow a feature while being completely generic
    """
    def __init__(
        self,
        experiment: Callable,
        find_relevant_point: Callable,
        update_window: Callable,
        predict_next_point: Callable | None = None,
        ):
        """_summary_

        Args:
            find_relevant_point (function): takes the data from measure as input and finds the relevant point
            predict_next_point (function): takes all the previously found points of interest and predicts the next
            update_window (function): with the predicted point as input, updates the window for the measurement
        """        
        self.experiment = Experiment()

        # self.qprogram = 
        # qprogram(index, window, kwargs)
        # partial
        self.find_relevant_point = find_relevant_point
        self.predict_next_point = predict_next_point
        self.update_window = update_window


    def get_parameter(self, alias: str, parameter: Parameter, channel_id: int | None = None):
        variable = self.experiment.get_parameter(alias, parameter, channel_id)
        return variable

    def set_parameter(self, alias: str, parameter: Parameter, value: int | float | int, channel_id: int | None = None):
        self.experiment.set_parameter(alias, parameter, value, channel_id)
        
    def execute_qprogram(self, bus_mapping: dict[str, str] | None = None, calibration: Calibration | None = None, debug: bool = False):
        self.experiment.execute_qprogram(self.qprogram, bus_mapping, calibration, debug)

    def run_tracker(self, alias:str, parameter: Parameter, values: list, initial_guess: float, bus_mapping: dict[str, str] | None = None, calibration: Calibration | None = None, plot:bool=False, plot_timeout:float=100) -> None: 
        """Runs the 

        Args:
            parameter (Parameter): parameter to be changed
            values (list): values for the parameter
            guess (float): first starting point for the window
        """  



        self.real_path = []
        self.guessed_path = []
        self.windows = []
        self.total_data = []
        guess = initial_guess
        for ii, value in enumerate(values):
            # Set the parameter 
            self.set_parameter(alias, parameter, value)
            
            # Update the window
            self.windows.append(self.update_window(guess))
            
            # Do the experiment
            measured_data = self.experiment.execute_qprogram(self.qprogram, bus_mapping, calibration)
            self.total_data.append(measured_data)
            
            # Measure the point of interest
            self.real_path.append(self.find_relevant_point(self.windows[-1], measured_data))
            
            # Predict the next point
            guess = self.predict_next_point(values[:ii+1], self.real_path)
            self.guessed_path.append(guess)
