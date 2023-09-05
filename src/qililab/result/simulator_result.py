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

"""SimulatorResult class."""
from dataclasses import dataclass

import numpy as np
from qutip import Qobj

from qililab.result.result import Result
from qililab.typings.enums import ResultName
from qililab.utils.factory import Factory


@Factory.register
@dataclass
class SimulatorResult(Result):  # pylint: disable=abstract-method
    """SimulatorResult class.

    Stores results from the simulator.

    Attributes:
        - name (string): results type
        - psi0 (Qobj): initial state (at time t=0)
        - states (list[Qobj]): calculated states
        - times (list[float]): timestamp for each state, in s.

    Notes:
        - self.probabilities() is not implemented
    """

    name = ResultName.SIMULATOR

    psi0: Qobj
    states: list[Qobj]
    times: list[float]

    def probabilities(self) -> dict[str, float]:
        """Probabilities of being in the ground and excited state.

        Returns arbitrary result.
        """
        # FIXME: need bypass when this is not implemented
        return {}

    def to_dict(self) -> dict:
        """Returns dict with class data.

        Notes:
            - Since Qobj is returned as object, PyYAML complains.
        """
        # FIXME: yaml.safe_dump fails with default implementation
        return {}

    @property
    def array(self) -> np.ndarray:
        return np.array([])
