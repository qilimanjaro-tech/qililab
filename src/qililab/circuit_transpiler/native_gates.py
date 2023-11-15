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
from qibo.gates.abstract import ParametrizedGate
from qibo.gates.gates import _Un_


class Drag(_Un_):
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

    def __init__(self, q: int, theta: float, phase: float, trainable: bool = True):
        super().__init__(q, trainable=trainable)
        self.name = "drag"
        self.nparams = 2
        self._theta, self._phi = None, None
        self.init_kwargs = {"theta": theta, "phase": phase, "trainable": trainable}
        self.parameter_names = ["theta", "phase"]
        self.parameters = theta, phase


class Wait(ParametrizedGate):
    """The Wait gate.

    Args:
        q (int): the qubit index.
        t (int): the time to wait (ns)
    """

    def __init__(self, q, t):
        super().__init__(trainable=True)
        self.name = "wait"
        self._controlled_gate = None
        self.target_qubits = (q,)

        self.parameters = t
        self.init_args = [q]
        self.init_kwargs = {"t": t}
