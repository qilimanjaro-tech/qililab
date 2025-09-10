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

import networkx as nx
from qibo.models import Circuit

from qililab.digital.routing._exceptions import ConnectivityError, PlacementError, TranspilerPipelineError
from qililab.digital.routing.abstract import Optimizer, Placer, Router
from qililab.digital.routing.asserts import assert_connectivity, assert_placement


def restrict_connectivity_qubits(connectivity: nx.Graph, qubits: list[str]):
    """Restrict the connectivity to selected qubits.

    Args:
        connectivity (:class:`networkx.Graph`): Hardware connectivity.
        qubits (list): List of qubits to select.

    Returns:
        (:class:`networkx.Graph`): New restricted connectivity.
    """
    if not set(qubits).issubset(set(connectivity.nodes)):
        raise ValueError("Some qubits are not in the original connectivity.")

    new_connectivity = nx.Graph()
    new_connectivity.add_nodes_from(qubits)
    new_edges = [edge for edge in connectivity.edges if edge[0] in qubits and edge[1] in qubits]
    new_connectivity.add_edges_from(new_edges)

    if not nx.is_connected(new_connectivity):
        raise ValueError("New connectivity graph is not connected.")

    return new_connectivity


class Passes:
    """Define a transpiler pipeline consisting of smaller transpiler steps that are applied sequentially:

    Args:
        passes (list, optional): List of transpiler passes to be applied sequentially.
            If ``None``, default transpiler will be used. Defaults to ``None``.
        connectivity (:class:`networkx.Graph`, optional): Hardware connectivity.
        native_gates (:class:`qibo.transpiler.unroller.NativeGates`, optional): Native gates supported by the hardware.
            Defaults to :class:`qibo.transpiler.unroller.NativeGates.default()`.
        on_qubits (list, optional): List of qubits to be used in the transpiler.
            If ``None``, all qubits in the connectivity will be used. Defaults to ``None``.
    """

    def __init__(
        self,
        passes: list = None,
        connectivity: nx.Graph = None,
        on_qubits: list = None,
    ):
        if on_qubits is not None:
            connectivity = restrict_connectivity_qubits(connectivity, on_qubits)
        self.connectivity = connectivity
        self.passes = [] if passes is None else passes

    def __call__(self, circuit):
        """Apply the transpiler pipeline to the circuit.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be transpiled.

        Returns:
            (:class:`qibo.models.circuit.Circuit`, dict): Transpiled circuit and final logical-physical qubit mapping.
        """

        final_layout = None
        for transpiler_pass in self.passes:
            if isinstance(transpiler_pass, Optimizer):
                transpiler_pass.connectivity = self.connectivity
                circuit = transpiler_pass(circuit)
            elif isinstance(transpiler_pass, Placer):
                transpiler_pass.connectivity = self.connectivity
                final_layout = transpiler_pass(circuit)
            elif isinstance(transpiler_pass, Router):
                transpiler_pass.connectivity = self.connectivity
                circuit, final_layout = transpiler_pass(circuit)
            else:
                raise TranspilerPipelineError(f"Unrecognised transpiler pass: {transpiler_pass}")
        return circuit, final_layout

    def is_satisfied(self, circuit: Circuit):
        """Check if the circuit respects the hardware connectivity and native gates.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be checked.

        Returns:
            (bool): ``True`` if the circuit respects the hardware connectivity and native gates, ``False`` otherwise.
        """
        try:
            assert_placement(circuit=circuit, connectivity=self.connectivity)
            assert_connectivity(circuit=circuit, connectivity=self.connectivity)
            return True
        except (ConnectivityError, PlacementError, ValueError):
            return False
