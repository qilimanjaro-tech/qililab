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

from typing import Any, Callable

from qililab.analog.fluqe_parameter import FluqeParameter


class Qubit2LevelTranspiler:
    """Implementation of the transpiler for the 2 level qubit. This is done mainly by inverting the same functions
    used in the single_qubit_2level emulator model.

    Args:
        epsilon_model (Callable): epsilon model
        delta_model (Callable): delta model

    Calling an instance of this class returns the fluxes phix, phiz for some given Delta, epsilon.
    """

    def __init__(self, epsilon_model: Callable, delta_model: Callable):
        """Init method. See class description for more details"""

        self.delta_model = delta_model
        self.epsilon_model = epsilon_model

        # Magnetic energy bias (epsilon)
        self.epsilon = FluqeParameter(name="epsilon", set_method=self._set_epsilon)
        # Qubit gap (delta)
        self.delta = FluqeParameter(name="delta", set_method=self._set_delta)
        # flux parameters
        self.phiz = FluqeParameter(name="phiz")
        self.phix = FluqeParameter(name="phix")

    def __call__(self, delta: float, epsilon: float) -> tuple[Any, Any]:
        """Transpiles Delta and Epsilon to phix, phiz"""
        self.delta(delta)
        self.epsilon(epsilon)
        return self.phix(), self.phiz()

    def _set_delta(self, delta):
        # sets the value of delta via raw and updates phix accordingly
        self.phix.set_raw(self.delta_model(delta))
        return delta

    def _set_epsilon(self, epsilon):
        """sets the value of epsilon via raw and updates phiz accordingly. Does not update phix
        since this is meant to be used in the transpiler in conjunction with setting delta (which
        already updates phix)
        """
        self.phiz.set_raw(self.epsilon_model(phix=self.phix(), epsilon=epsilon))
        return epsilon
