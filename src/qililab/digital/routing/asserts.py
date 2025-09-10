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
from qibo import gates
from qibo.models.circuit import Circuit

# from qibo.quantum_info.random_ensembles import random_statevector
from qililab.digital.routing._exceptions import ConnectivityError, PlacementError


def assert_placement(circuit: Circuit, connectivity: nx.Graph):
    """Check if the layout of the circuit is consistent with the circuit and connectivity graph.

    Args:
        circuit (:class:`qibo.models.circuit.Circuit`): Circuit to check.
        connectivity (:class:`networkx.Graph`, optional): Hardware connectivity.
    """
    if connectivity is None:
        raise ValueError("Connectivity graph is not provided")

    if circuit.nqubits != len(circuit.wire_names) or circuit.nqubits != len(connectivity.nodes):
        raise PlacementError(
            f"Number of qubits in the circuit ({circuit.nqubits}) "
            + f"does not match the number of qubits in the layout ({len(circuit.wire_names)}) "
            + f"or the connectivity graph ({len(connectivity.nodes)}).",
        )
    if set(circuit.wire_names) != set(connectivity.nodes):
        raise PlacementError("Some physical qubits in the layout may be missing or duplicated.")


def assert_connectivity(connectivity: nx.Graph, circuit: Circuit):
    """Assert if a circuit can be executed on Hardware.

    No gates acting on more than two qubits.
    All two-qubit operations can be performed on hardware.

    Args:
        circuit (:class:`qibo.models.circuit.Circuit`): Circuit to check.
        connectivity (:class:`networkx.Graph`): Hardware connectivity.
    """
    layout = circuit.wire_names
    for gate in circuit.queue:
        if len(gate.qubits) > 2 and not isinstance(gate, gates.M):
            raise ConnectivityError(f"{gate.name} acts on more than two qubits.")
        if len(gate.qubits) == 2:
            physical_qubits = (layout[gate.qubits[0]], layout[gate.qubits[1]])
            if physical_qubits not in connectivity.edges:
                raise ConnectivityError(
                    f"The circuit does not respect the connectivity. {gate.name} acts on {physical_qubits} but only the following qubits are directly connected: {connectivity.edges}.",
                )
