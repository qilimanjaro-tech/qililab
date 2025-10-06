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

from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings

from .circuit_transpiler_passes import (
    AddPhasesToDragsFromRZAndCZPass,
    CancelIdentityPairsPass,
    CanonicalBasisToNativeSetPass,
    CircuitToCanonicalBasisPass,
    CircuitTranspilerPass,
    CustomLayoutPass,
    FuseSingleQubitGatesPass,
    SabreLayoutPass,
    SabreSwapPass,
    TranspilationContext,
)


class DigitalTranspilationConfig: ...


class CircuitTranspiler:
    def __init__(
        self,
        settings: DigitalCompilationSettings,
        pipeline: list[CircuitTranspilerPass] | None = None,
        context: TranspilationContext | None = None,
        qubit_mapping: dict[int, int] | None = None,
    ) -> None:
        self._settings = settings
        self._topology = self._build_topology_graph(settings)

        layout_routing_passes: list[CircuitTranspilerPass] = (
            [SabreLayoutPass(self._topology), SabreSwapPass(self._topology)]
            if qubit_mapping is None
            else [CustomLayoutPass(self._topology, qubit_mapping)]
        )

        # Main pipeline
        self._pipeline = pipeline or [
            CancelIdentityPairsPass(),
            CircuitToCanonicalBasisPass(),
            FuseSingleQubitGatesPass(),
            *layout_routing_passes,
            CircuitToCanonicalBasisPass(),
            FuseSingleQubitGatesPass(),
            CanonicalBasisToNativeSetPass(),
            AddPhasesToDragsFromRZAndCZPass(self._settings),
        ]
        self._context = context or TranspilationContext()

        for p in self._pipeline:
            p.attach_context(self._context)

    def _build_topology_graph(self, settings: DigitalCompilationSettings) -> PyGraph:
        physical_nqubits = max(max(pair) for pair in settings.topology) + 1
        topology = PyGraph()
        topology.add_nodes_from(range(physical_nqubits))
        for a, b in settings.topology:
            topology.add_edge(a, b, None)
        return topology

    @property
    def context(self) -> TranspilationContext:
        return self._context

    def run(self, circuit: Circuit) -> Circuit:
        for transpiler_pass in self._pipeline:
            circuit = deepcopy(circuit)
            circuit = transpiler_pass.run(circuit)
        return circuit
