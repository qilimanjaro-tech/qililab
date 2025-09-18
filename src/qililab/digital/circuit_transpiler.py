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

from copy import deepcopy

from qilisdk.digital import Circuit
from rustworkx import PyGraph

from .circuit_transpiler_passes import (
    CanonicalBasisToNativeSetPass,
    CircuitToCanonicalBasisPass,
    CircuitTranspilerPass,
    FuseSingleQubitGatesPass,
    SabreLayoutPass,
    SabreSwapPass,
    TranspilationContext,
)


class DigitalTranspilationConfig: ...


class CircuitTranspiler:
    def __init__(
        self,
        topology: PyGraph,
        pipeline: list[CircuitTranspilerPass] | None = None,
        context: TranspilationContext | None = None,
    ) -> None:
        self._topology = topology
        self._pipeline = pipeline or [
            CircuitToCanonicalBasisPass(),
            FuseSingleQubitGatesPass(),
            # CancelPairsOfHermitianGatesPass(),
            SabreLayoutPass(self._topology),
            SabreSwapPass(self._topology),
            CircuitToCanonicalBasisPass(),
            FuseSingleQubitGatesPass(),
            CanonicalBasisToNativeSetPass(),
        ]
        self._context = context or TranspilationContext()

        for p in self._pipeline:
            p.attach_context(self._context)

    @property
    def context(self) -> TranspilationContext:
        return self._context

    def run(self, circuit: Circuit) -> Circuit:
        for transpiler_pass in self._pipeline:
            circuit = deepcopy(circuit)
            circuit = transpiler_pass.run(circuit)
        return circuit
