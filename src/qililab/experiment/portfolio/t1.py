# pylint: disable=cyclic-import
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

"""This file contains a pre-defined version of a T1 experiment."""
import numpy as np
from qibo.gates import M
from qibo.models import Circuit

import qililab as ql
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop

from .experiment_analysis import ExperimentAnalysis
from .fitting_models import Exp


class T1(ExperimentAnalysis, Exp):
    """Experiment to determine the T1 value of a qubit.

    The value of T1 is measured through the following sequence of operations:
        1. Prepare the qubit in the excited state by sending a π-pulse to the qubit.
        2. Wait some time t.
        3. Measure the state of the qubit.

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        wait_loop_values (numpy.ndarray): array of values to loop through in the experiment, which modifies the t parameter of the Wait gate
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 200000.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 10000.
    """

    def __init__(
        self,
        qubit: int,
        platform: Platform,
        wait_loop_values: np.ndarray,
        repetition_duration=200000,
        hardware_average=10000,
    ):
        # Define circuit used in this experiment
        circuit = Circuit(qubit + 1)
        circuit.add(ql.Drag(q=qubit, theta=np.pi, phase=0))
        circuit.add(ql.Wait(q=qubit, t=0))
        circuit.add(M(qubit))

        # Define loop over wait duration
        loop = Loop(alias="2", parameter=Parameter.GATE_PARAMETER, values=wait_loop_values)

        # Define experiment options
        experiment_options = ExperimentOptions(
            name="t1",
            loops=[loop],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=[circuit],
            options=experiment_options,
        )
