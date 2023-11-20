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

"""This file contains a pre-defined version of the flux spectroscopy experiment."""
import numpy as np
from qibo.gates import M
from qibo.models import Circuit

import qililab as ql  # pylint: disable=cyclic-import
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop

from .experiment_analysis import ExperimentAnalysis
from .fitting_models import Exp


class T2Echo(ExperimentAnalysis, Exp):
    """Class used to run a T2Echo experiment on the given qubit. The experiment performs the following circuit:

    1. Prepare the qubit in the ∣-i⟩ state by sending a π/2-pulse to the qubit
    2. Wait some time t
    3. Send a π-pulse to the qubit
    4. Wait some time t
    5. Send a π/2-pulse to the qubit
    6. Measure the qubit

    Args:
        platform (Platform): platform used to run the experiment.
        qubit (int): qubit index used in the experiment.
        wait_loop_values (ndarray): array of time values to wait for the `Wait` gates, the same value is used on both
            gates.
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Default to 10000.
        measurement_buffer (int, optional): time to wait before taking the measurement. Default to 100.
        hardware_average (int, optional): number of repetitions used to average the result. Default to 10000.
    """

    def __init__(
        self,
        qubit: int,
        platform: Platform,
        wait_loop_values: np.ndarray,
        repetition_duration=10000,
        measurement_buffer=100,
        hardware_average=10000,
    ):
        self.wait_loop_values = wait_loop_values
        self.t2 = None
        # Define Circuit to execute
        circuit = Circuit(qubit + 1)
        circuit.add(ql.Drag(q=qubit, theta=np.pi / 2, phase=0))
        circuit.add(ql.Wait(qubit, t=0))
        circuit.add(ql.Drag(q=qubit, theta=np.pi, phase=0))
        circuit.add(ql.Wait(qubit, t=0))
        circuit.add(ql.Drag(q=qubit, theta=np.pi / 2, phase=0))
        circuit.add(ql.Wait(qubit, t=measurement_buffer))
        circuit.add(M(qubit))

        # Alias of loops reference the wait parameters, looping over wait times.
        first_wait_loop = Loop(alias="2", parameter=Parameter.GATE_PARAMETER, values=wait_loop_values)
        second_wait_loop = Loop(alias="5", parameter=Parameter.GATE_PARAMETER, values=wait_loop_values)

        experiment_options = ExperimentOptions(
            name="t2echo",
            loops=[first_wait_loop, second_wait_loop],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
        )

        super().__init__(
            platform=platform,
            circuits=[circuit],
            options=experiment_options,
        )

    def fit(self, p0: tuple | None = (-52, 2000, 0)):
        """
        Fitting function for the T2Echo class. Calls the ExperimentAnalysis.fit() and returns the fitted T2 value.

        Args:
            p0 (tuple, optional): Initial guess for the parameters. Default to (-52, 2000, 0).
        """
        fitted_params = super().fit(p0=p0)
        self.t2 = 2 * fitted_params[1]
        return self.t2
