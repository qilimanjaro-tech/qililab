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

"""File containing the supported native gates."""

from typing import ClassVar

import numpy as np
from qilisdk.core import Parameter
from qilisdk.digital.gates import BasicGate
from qilisdk.yaml import yaml


@yaml.register_class
class Rmw(BasicGate):
    r"""Native drag pulse dummy class.
    Inherits from qibo unitary gates class

    The native gate is a drag pulse
    .. math::

        R_{MW}(\theta, \phi) = Z_\phi X_\theta Z_{-\phi}

    Please note that the negative Z rotations is applied first! The circuit drawing of this gate looks like the
    following:

    .. math::

        --|RZ(-phi)|--|RX(theta)|--|RZ(phi)|--

    Together with virtual Z gates, this allows us to perform any single-qubit gate, since any
    such gate can be expressed as a unitary
    .. math::

        U(\theta,\phi,\lambda) = Z_\phi X_\theta Z_\lambda &= R_{MW}(\theta, \phi)Z_{\lambda+\phi} &=
        Z_{\phi+\lambda}R_{MW}(\theta, -\lambda)

    Args:
        q (int): qubit where the gate is applied
        theta (float): theta angle of rotation in radians
        phase (float): phase of  the Drag pulse
        trainable (bool): whether parameters are trainable (set to false)
    """

    PARAMETER_NAMES: ClassVar[list[str]] = ["theta", "phase"]

    def __init__(self, qubit: int, *, theta: float, phase: float):
        super().__init__(
            target_qubits=(qubit,),
            parameters={
                "theta": theta if isinstance(theta, Parameter) else Parameter("theta", theta),
                "phase": phase if isinstance(phase, Parameter) else Parameter("phase", phase),
            },
        )

    @property
    def name(self) -> str:
        return "Rmw"

    @property
    def theta(self) -> float:
        return self.get_parameters()["theta"]

    @property
    def phase(self) -> float:
        return self.get_parameters()["phase"]

    def _generate_matrix(self) -> np.ndarray:
        # TODO: What is the matrix?
        return np.array([])
