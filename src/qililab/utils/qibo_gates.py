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

from qibo.gates.abstract import ParametrizedGate


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
