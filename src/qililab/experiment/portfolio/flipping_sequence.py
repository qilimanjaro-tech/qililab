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

"""This file contains a pre-defined version of a flipping sequence experiment."""
import numpy as np
from qibo.gates import RX, M, X
from qibo.models import Circuit

from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop

from .experiment_analysis import ExperimentAnalysis
from .fitting_models import Cos


class FlippingSequence(ExperimentAnalysis, Cos):
    """Class used to run a flipping sequence experiment on the given qubit.

    This experiment creates multiple circuits, each of which uses an RX(pi/2) gate to send the qubit to the equator of
    the Bloch sphere, and then applies N R(2pi) gates to flip the qubit around the x axis N times. Given that the
    amplitude of the X gate is not well calibrated, the qubit will move towards the ground or the excited state.

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        loop_values (numpy.ndarray): array of values to loop through in the experiment, which determines the number of flips
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 10000.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 10000.
    """

    def __init__(
        self,
        platform: Platform,
        qubit: int,
        loop_values: np.ndarray,
        repetition_duration=10000,
        hardware_average=10000,
    ):
        # Define circuits used in this experiment
        loop = Loop(alias="N", parameter=Parameter.NUM_FLIPS, values=loop_values)
        circuits = []
        for n in loop.values:
            circuit = Circuit(1)
            circuit.add(RX(qubit, theta=np.pi / 2))
            for _ in range(n):
                circuit.add(X(qubit))
                circuit.add(X(qubit))
            circuit.add(M(qubit))
            circuits.append(circuit)

        _, control_bus, readout_bus = platform._get_bus_by_qubit_index(qubit)

        experiment_options = ExperimentOptions(
            name="Flipping Sequence",
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=circuits,
            options=experiment_options,
            control_bus=control_bus,
            readout_bus=readout_bus,
            experiment_loop=loop,
        )
