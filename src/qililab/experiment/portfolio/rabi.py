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

"""This file contains a pre-defined version of a rabi experiment."""
import numpy as np
from qibo.gates import M, X
from qibo.models import Circuit

from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop

from .experiment_analysis import ExperimentAnalysis
from .fitting_models import Cos


class Rabi(ExperimentAnalysis, Cos):
    """Class used to run a rabi experiment on the given qubit. This experiment modifies the amplitude of the pulse
    associated to the X gate.

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        loopvalues (numpy.ndarray): array of values to loop through in the experiment, which modifies the amplitude of X gate
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 10000.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 10000.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        platform: Platform,
        qubit: int,
        loop_values: np.ndarray,
        repetition_duration=10000,
        hardware_average=10000,
    ):
        # Define circuit used in this experiment
        circuit = Circuit(1)
        circuit.add(X(qubit))
        circuit.add(M(qubit))

        _, control_bus, readout_bus = platform._get_bus_by_qubit_index(qubit)

        # Define loop used in the experiment
        loop = Loop(alias="X", parameter=Parameter.AMPLITUDE, values=loop_values)

        experiment_options = ExperimentOptions(
            name="Rabi",
            loops=[loop],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=[circuit],
            options=experiment_options,
            control_bus=control_bus,
            readout_bus=readout_bus,
        )
