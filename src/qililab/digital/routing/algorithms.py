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

import random
from typing import Optional, Union

import networkx as nx
import numpy as np
from qibo import Circuit, gates

from qililab.digital.routing._exceptions import ConnectivityError, PlacementError
from qililab.digital.routing.abstract import Optimizer, Placer, Router
from qililab.digital.routing.asserts import assert_placement
from qililab.digital.routing.blocks import Block, CircuitBlocks


class Preprocessing(Optimizer):
    """Pad the circuit with unused qubits to match the number of physical qubits.

    Args:
        connectivity (:class:`networkx.Graph`): Hardware connectivity.
    """

    def __init__(self, connectivity: Optional[nx.Graph] = None):
        self.connectivity = connectivity

    def __call__(self, circuit: Circuit) -> Circuit:
        if not all(qubit in self.connectivity.nodes for qubit in circuit.wire_names):
            raise ValueError(
                "Some wire_names in the circuit are not in the connectivity graph.",
            )

        physical_qubits = self.connectivity.number_of_nodes()
        logical_qubits = circuit.nqubits
        if logical_qubits > physical_qubits:
            raise ValueError(
                f"The number of qubits in the circuit ({logical_qubits}) "
                + f"can't be greater than the number of physical qubits ({physical_qubits}).",
            )
        if logical_qubits == physical_qubits:
            return circuit
        new_wire_names = circuit.wire_names + list(self.connectivity.nodes - circuit.wire_names)
        new_circuit = Circuit(nqubits=physical_qubits, wire_names=new_wire_names)
        for gate in circuit.queue:
            new_circuit.add(gate)
        return new_circuit


def _find_gates_qubits_pairs(circuit: Circuit):
    """Helper method for :meth:`qibo.transpiler.placer`.
    Translate circuit into a list of pairs of qubits to be used by the router and placer.

    Args:
        circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be translated.

    Returns:
        (list): Pairs of qubits targeted by two qubits gates.
    """
    gates_qubits_pairs = []
    for gate in circuit.queue:
        if isinstance(gate, gates.M):
            pass
        elif len(gate.qubits) == 2:
            gates_qubits_pairs.append(sorted(gate.qubits))
        elif len(gate.qubits) >= 3:
            raise ValueError("Gates targeting more than 2 qubits are not supported")
    return gates_qubits_pairs


def _find_connected_qubit(qubits, queue, error, mapping):
    """Helper method for :meth:`qibo.transpiler.router.StarConnectivityRouter`
    and :meth:`qibo.transpiler.router.StarConnectivityPlacer`.

    Finds which qubit should be mapped to hardware middle qubit
    by looking at the two-qubit gates that follow.
    """
    possible_qubits = {qubits[0], qubits[1]}
    for next_gate in queue:
        if len(next_gate.qubits) > 2:
            raise error("Gates targeting more than 2 qubits are not supported")
        if len(next_gate.qubits) == 2:
            possible_qubits &= {
                mapping[next_gate.qubits[0]],
                mapping[next_gate.qubits[1]],
            }

            if len(possible_qubits) == 0:
                return qubits[0]
            if len(possible_qubits) == 1:
                return possible_qubits.pop()

    return qubits[0]


class StarConnectivityPlacer(Placer):
    """Find an optimized qubit placement for the following connectivity:

             q
             |
        q -- q -- q
             |
             q

    Args:
        connectivity (:class:`networkx.Graph`): Star connectivity graph.
    """

    def __init__(self, connectivity: Optional[nx.Graph] = None):
        self.connectivity = connectivity
        self.middle_qubit = None

    def __call__(self, circuit: Circuit):
        """Apply the transpiler transformation on a given circuit.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): The original Qibo circuit to transform.
                Only single qubit gates and two qubits gates are supported by the router.
        """
        assert_placement(circuit, self.connectivity)
        self._check_star_connectivity()

        middle_qubit_idx = circuit.wire_names.index(self.middle_qubit)
        wire_names = circuit.wire_names.copy()

        for i, gate in enumerate(circuit.queue):
            if len(gate.qubits) > 2:
                raise PlacementError("Gates targeting more than 2 qubits are not supported")
            if len(gate.qubits) == 2:
                if middle_qubit_idx not in gate.qubits:
                    new_middle = _find_connected_qubit(
                        gate.qubits,
                        circuit.queue[i + 1 :],
                        error=PlacementError,
                        mapping=list(range(circuit.nqubits)),
                    )

                    (
                        wire_names[middle_qubit_idx],
                        wire_names[new_middle],
                    ) = (
                        wire_names[new_middle],
                        wire_names[middle_qubit_idx],
                    )
                    break

        circuit.wire_names = wire_names

    def _check_star_connectivity(self):
        """Check if the connectivity graph is a star graph."""
        for node in self.connectivity.nodes:
            if self.connectivity.degree(node) == 4:
                self.middle_qubit = node
            elif self.connectivity.degree(node) != 1:
                raise ValueError("This connectivity graph is not a star graph.")


class ReverseTraversal(Placer):
    """
    Places qubits based on the algorithm proposed in Reference [1].

    Compatible with all the available ``Router``s.

    Args:
        connectivity (:class:`networkx.Graph`): Hardware connectivity.
        routing_algorithm (:class:`qibo.transpiler.abstract.Router`): Router to be used.
        depth (int, optional): Number of two-qubit gates to be considered for routing.
            If ``None`` just one backward step will be implemented.
            If depth is greater than the number of two-qubit gates in the circuit,
            the circuit will be routed more than once.
            Example: on a circuit with four two-qubit gates :math:`A-B-C-D`
            using depth :math:`d = 6`, the routing will be performed
            on the circuit :math:`C-D-D-C-B-A`.

    References:
        1. G. Li, Y. Ding, and Y. Xie,
        *Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices*.
        `arXiv:1809.02573 [cs.ET] <https://arxiv.org/abs/1809.02573>`_.
    """

    def __init__(
        self,
        routing_algorithm: Router,
        connectivity: Optional[nx.Graph] = None,
        depth: Optional[int] = None,
    ):
        self.connectivity = connectivity
        self.routing_algorithm = routing_algorithm
        self.depth = depth

    def __call__(self, circuit: Circuit):
        """Find the initial layout of the given circuit using Reverse Traversal placement.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be transpiled.
        """
        assert_placement(circuit, self.connectivity)
        self.routing_algorithm.connectivity = self.connectivity
        new_circuit = self._assemble_circuit(circuit)
        self._routing_step(new_circuit)

    def _assemble_circuit(self, circuit: Circuit):
        """Assemble a single circuit to apply Reverse Traversal placement based on depth.

        Example: for a circuit with four two-qubit gates :math:`A-B-C-D`
        using depth :math:`d = 6`, the function will return the circuit :math:`C-D-D-C-B-A`.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be assembled.

        Returns:
            (:class:`qibo.models.circuit.Circuit`): Assembled circuit to perform Reverse Traversal placement.
        """

        if self.depth is None:
            return circuit.invert()

        gates_qubits_pairs = _find_gates_qubits_pairs(circuit)
        circuit_gates = len(gates_qubits_pairs)
        if circuit_gates == 0:
            raise ValueError("The circuit must contain at least a two-qubit gate.")
        repetitions, remainder = divmod(self.depth, circuit_gates)

        assembled_gates_qubits_pairs = []
        for _ in range(repetitions):
            assembled_gates_qubits_pairs += gates_qubits_pairs[:]
            gates_qubits_pairs.reverse()
        assembled_gates_qubits_pairs += gates_qubits_pairs[0:remainder]

        new_circuit = Circuit(circuit.nqubits, wire_names=circuit.wire_names)
        for qubits in assembled_gates_qubits_pairs:
            # As only the connectivity is important here we can replace everything with CZ gates
            new_circuit.add(gates.CZ(qubits[0], qubits[1]))

        return new_circuit.invert()

    def _routing_step(self, circuit: Circuit):
        """Perform routing of the circuit.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be routed.
        """
        _, final_mapping = self.routing_algorithm(circuit)

        return final_mapping


class StarConnectivityRouter(Router):
    """Transforms an arbitrary circuit to one that can be executed on hardware.

    This transpiler produces a circuit that respects the following connectivity:

             q
             |
        q -- q -- q
             |
             q

    by adding SWAP gates when needed.

    Args:
        connectivity (:class:`networkx.Graph`): Star connectivity graph.
    """

    def __init__(self, connectivity: Optional[nx.Graph] = None):
        self.connectivity = connectivity
        self.middle_qubit = None

    def __call__(self, circuit: Circuit):
        """Apply the transpiler transformation on a given circuit.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): The original Qibo circuit to transform.
                Only single qubit gates and two qubits gates are supported by the router.
        """
        self._check_star_connectivity()
        assert_placement(circuit, self.connectivity)

        middle_qubit_idx = circuit.wire_names.index(self.middle_qubit)
        nqubits = circuit.nqubits
        new = Circuit(nqubits=nqubits, wire_names=circuit.wire_names)
        l2p = list(range(nqubits))

        for i, gate in enumerate(circuit.queue):
            routed_qubits = [l2p[q] for q in gate.qubits]

            if isinstance(gate, gates.M):
                new_gate = gates.M(*routed_qubits, **gate.init_kwargs)
                new_gate.result = gate.result
                new.add(new_gate)
                continue

            if len(routed_qubits) > 2:
                raise ConnectivityError("Gates targeting more than two qubits are not supported.")

            if len(routed_qubits) == 2 and middle_qubit_idx not in routed_qubits:
                # find which qubit should be moved
                new_middle = _find_connected_qubit(
                    routed_qubits,
                    circuit.queue[i + 1 :],
                    error=ConnectivityError,
                    mapping=l2p,
                )

                new.add(gates.SWAP(new_middle, middle_qubit_idx))
                idx1, idx2 = l2p.index(middle_qubit_idx), l2p.index(new_middle)
                l2p[idx1], l2p[idx2] = l2p[idx2], l2p[idx1]

            routed_qubits = [l2p[q] for q in gate.qubits]

            # add gate to the hardware circuit
            if isinstance(gate, gates.Unitary):
                # gates.Unitary requires matrix as first argument
                matrix = gate.init_args[0]
                new.add(gate.__class__(matrix, *routed_qubits, **gate.init_kwargs))
            else:
                new.add(gate.__class__(*routed_qubits, **gate.init_kwargs))
        return new, {circuit.wire_names[i]: l2p[i] for i in range(nqubits)}

    def _check_star_connectivity(self):
        """Check if the connectivity graph is a star graph."""
        for node in self.connectivity.nodes:
            if self.connectivity.degree(node) == 4:
                self.middle_qubit = node
            elif self.connectivity.degree(node) != 1:
                raise ValueError("This connectivity graph is not a star graph.")


class CircuitMap:
    """Class that stores the circuit and physical-logical mapping during routing.

    Also implements the initial two-qubit block decompositions.

    Args:
        circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be routed.
        blocks (:class:`qibo.transpiler.blocks.CircuitBlocks`, optional): Circuit block representation.
            If ``None``, the blocks will be computed from the circuit. Defaults to ``None``.
    """

    def __init__(
        self,
        circuit: Optional[Circuit] = None,
        blocks: Optional[CircuitBlocks] = None,
        temp: Optional[bool] = False,
    ):
        self._p2l: list[int] = []
        self._l2p: list[int] = []

        self._temporary = temp
        if self._temporary:
            return
        if circuit is None:
            raise ValueError("Circuit must be provided.")
        if blocks is not None:
            self.circuit_blocks = blocks
        else:
            self.circuit_blocks = CircuitBlocks(circuit, index_names=True)

        self.nqubits = circuit.nqubits
        self._routed_blocks = CircuitBlocks(Circuit(circuit.nqubits, wire_names=circuit.wire_names))
        self._swaps = 0

        self.wire_names = circuit.wire_names.copy()
        self.physical_to_logical = list(range(self.nqubits))

    @property
    def physical_to_logical(self):
        """Returns the physical to logical qubit mapping."""
        return self._p2l

    @property
    def logical_to_physical(self):
        """Returns the logical to physical qubit mapping."""
        return self._l2p

    @physical_to_logical.setter
    def physical_to_logical(self, p2l_map: list):
        """Sets the physical to logical qubit mapping and updates the logical to physical mapping.

        Args:
            p2l_map (list): Physical to logical mapping.
        """
        self._p2l = p2l_map.copy()
        self._l2p = [0] * len(self._p2l)
        for i, l in enumerate(self._p2l):
            self._l2p[l] = i

    @logical_to_physical.setter
    def logical_to_physical(self, l2p_map: list):
        """Sets the logical to physical qubit mapping and updates the physical to logical mapping.

        Args:
            l2p_map (list): Logical to physical mapping.
        """
        self._l2p = l2p_map.copy()
        self._p2l = [0] * len(self._l2p)
        for i, p in enumerate(self._l2p):
            self._p2l[p] = i

    def _update_mappings_swap(self, logical_swap: tuple, physical_swap: tuple):
        """Updates the qubit mappings after applying a SWAP gate.

        Args:
            logical_swap (tuple[int]): The indices of the logical qubits to be swapped.
            physical_swap (tuple[int]): The indices of the corresponding physical qubits to be swapped.
        """
        self._p2l[physical_swap[0]], self._p2l[physical_swap[1]] = (
            logical_swap[1],
            logical_swap[0],
        )
        self._l2p[logical_swap[0]], self._l2p[logical_swap[1]] = (
            physical_swap[1],
            physical_swap[0],
        )

    def blocks_logical_qubits_pairs(self):
        """Returns a list containing the logical qubit pairs of each block."""
        return [block.qubits for block in self.circuit_blocks()]

    def execute_block(self, block: Block):
        """Executes a block by removing it from the circuit representation
        and adding it to the routed circuit.

        Method works in-place.

        Args:
            block (:class:`qibo.transpiler.blocks.Block`): Block to be removed.
        """
        self._routed_blocks.add_block(block.on_qubits(self.get_physical_qubits(block)))
        self.circuit_blocks.remove_block(block)

    def routed_circuit(self, circuit_kwargs: Optional[dict] = None):
        """Returns the routed circuit.

        Args:
            circuit_kwargs (dict): Original circuit init_kwargs.

        Returns:
            :class:`qibo.models.circuit.Circuit`: Routed circuit.
        """
        return self._routed_blocks.circuit(circuit_kwargs=circuit_kwargs)

    def final_layout(self):
        """Returns the final physical-logical qubits mapping."""

        return {self.wire_names[i]: self._l2p[i] for i in range(self.nqubits)}

    def update(self, logical_swap: tuple):
        """Updates the qubit mapping after applying a ``SWAP``

        Adds the :class:`qibo.gates.gates.SWAP` gate to the routed blocks.
        Method works in-place.

        Args:
            swap (tuple): Tuple containing the logical qubits to be swapped.
        """

        physical_swap = self.logical_pair_to_physical(logical_swap)
        if not self._temporary:
            self._routed_blocks.add_block(Block(qubits=physical_swap, gates=[gates.SWAP(*physical_swap)]))
            self._swaps += 1

        self._update_mappings_swap(logical_swap, physical_swap)

    def undo(self):
        """Undo the last swap. Method works in-place."""
        last_swap_block = self._routed_blocks.return_last_block()
        physical_swap = last_swap_block.qubits
        logical_swap = self._p2l[physical_swap[0]], self._p2l[physical_swap[1]]
        self._routed_blocks.remove_block(last_swap_block)
        self._swaps -= 1

        self._update_mappings_swap(logical_swap, physical_swap)

    def get_physical_qubits(self, block: Union[int, Block]):
        """Returns the physical qubits where a block is acting on.

        Args:
            block (int or :class:`qibo.transpiler.blocks.Block`): Block to be analysed.

        Returns:
            tuple: Physical qubit numbers where a block is acting on.
        """
        _block: Block = self.circuit_blocks.search_by_index(block) if isinstance(block, int) else block

        return tuple(self._l2p[q] for q in _block.qubits)

    def logical_pair_to_physical(self, logical_qubits: tuple):
        """Returns the physical qubits associated to the logical qubit pair.

        Args:
            logical_qubits (tuple): Logical qubit pair.

        Returns:
            tuple: Physical qubit numbers associated to the logical qubit pair.
        """
        return self._l2p[logical_qubits[0]], self._l2p[logical_qubits[1]]


class Sabre(Router):
    """Routing algorithm proposed in Ref [1].

    Args:
        connectivity (:class:`networkx.Graph`): Hardware chip connectivity.
        lookahead (int, optional): Lookahead factor, how many dag layers will be considered
            in computing the cost. Defaults to :math:`2`.
        decay_lookahead (float, optional): Value in interval :math:`[0, 1]`.
            How the weight of the distance in the dag layers decays in computing the cost.
            Defaults to :math:`0.6`.
        delta (float, optional): Defines the number of SWAPs vs depth trade-off by deciding
            how the algorithm tends to select non-overlapping SWAPs.
            Defaults to math:`10^{-3}`.
        seed (int, optional): Seed for the candidate random choice as tiebraker.
            Defaults to ``None``.
        swap_threshold (float, optional): Limits the number of added SWAPs in every routing iteration.
            This threshold is multiplied by the length of the longest path in the circuit connectivity.
            If the number of added SWAPs exceeds the threshold before a gate is routed,
            shortestpath routing is applied.
            Defaults to :math:`1.5`.

    References:
        1. G. Li, Y. Ding, and Y. Xie,
        *Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices*.
        `arXiv:1809.02573 [cs.ET] <https://arxiv.org/abs/1809.02573>`_.
    """

    def __init__(
        self,
        connectivity: Optional[nx.Graph] = None,
        lookahead: int = 2,
        decay_lookahead: float = 0.6,
        delta: float = 0.001,
        swap_threshold: float = 1.5,
        seed: Optional[int] = None,
    ):
        self.connectivity = connectivity
        self.lookahead = lookahead
        self.decay = decay_lookahead
        self.delta = delta
        self.swap_threshold = swap_threshold
        # self._delta_register = None
        # self._dist_matrix = None
        # self._dag = None
        # self._front_layer = None
        # self.circuit_map = None
        # self._memory_map = None
        # self._final_measurements = None
        self._temp_added_swaps: list[list[int]] = []
        random.seed(seed)

    def __call__(self, circuit: Circuit):
        """Route the circuit.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be routed.

        Returns:
            (:class:`qibo.models.circuit.Circuit`, dict): Routed circuit and final logical-physical qubit mapping.
        """
        assert_placement(circuit, self.connectivity)
        self._preprocessing(circuit=circuit)
        longest_path = np.max(self._dist_matrix)

        while self._dag.number_of_nodes() != 0:
            execute_block_list = self._check_execution()
            if execute_block_list is not None:
                self._execute_blocks(execute_block_list)
            else:
                self._find_new_mapping()

            # If the number of added swaps is too high, the algorithm is stuck.
            # Reset the circuit to the last saved state and make the nearest gate executable by manually adding SWAPs.
            if len(self._temp_added_swaps) > self.swap_threshold * longest_path:  # threshold is arbitrary
                while self._temp_added_swaps:
                    self._temp_added_swaps.pop()
                    self.circuit_map.undo()
                self._temp_added_swaps = []
                self._shortest_path_routing()

        circuit_kwargs = circuit.init_kwargs
        routed_circuit = self.circuit_map.routed_circuit(circuit_kwargs=circuit_kwargs)
        if self._final_measurements is not None:
            routed_circuit = self._append_final_measurements(routed_circuit=routed_circuit)

        return routed_circuit, self.circuit_map.final_layout()

    @property
    def added_swaps(self):
        """Returns the number of SWAP gates added to the circuit during routing."""
        return self.circuit_map._swaps

    def _preprocessing(self, circuit: Circuit):
        """The following objects will be initialised:
            - circuit: class to represent circuit and to perform logical-physical qubit mapping.
            - _final_measurements: measurement gates at the end of the circuit.
            - _dist_matrix: matrix reporting the shortest path lengh between all node pairs.
            - _dag: direct acyclic graph of the circuit based on commutativity.
            - _memory_map: list to remember previous SWAP moves.
            - _front_layer: list containing the blocks to be executed.
            - _delta_register: list containing the special weigh added to qubits
                to prevent overlapping swaps.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be preprocessed.
        """

        self.connectivity = nx.relabel_nodes(self.connectivity, {v: i for i, v in enumerate(circuit.wire_names)})

        copied_circuit = circuit.copy(deep=True)
        self._final_measurements = self._detach_final_measurements(copied_circuit)
        self.circuit_map = CircuitMap(copied_circuit)
        self._dist_matrix = nx.floyd_warshall_numpy(self.connectivity)
        self._dag = _create_dag(self.circuit_map.blocks_logical_qubits_pairs())
        self._memory_map: list[list[int]] = []
        self._update_dag_layers()
        self._update_front_layer()
        self._delta_register = [1.0 for _ in range(circuit.nqubits)]

    def _detach_final_measurements(self, circuit: Circuit):
        """Detach measurement gates at the end of the circuit for separate handling."""
        final_measurements = []
        for gate in circuit.queue[::-1]:
            if isinstance(gate, gates.M):
                final_measurements.append(gate)
                circuit.queue.remove(gate)
            else:
                break
        if not final_measurements:
            return None
        return final_measurements[::-1]

    def _append_final_measurements(self, routed_circuit: Circuit):
        """Appends final measurment gates on the correct qubits conserving the measurement register.

        Args:
            routed_circuit (:class:`qibo.models.circuit.Circuit`): Original circuit.

        Returns:
            (:class:`qibo.models.circuit.Circuit`) Routed circuit.
        """
        for measurement in self._final_measurements:
            original_qubits = measurement.qubits
            routed_qubits = [self.circuit_map.logical_to_physical[qubit] for qubit in original_qubits]
            routed_circuit.add(measurement.on_qubits(dict(zip(original_qubits, routed_qubits))))
        return routed_circuit

    def _update_dag_layers(self):
        """Update dag layers and put them in topological order.

        Method works in-place.
        """
        for layer, nodes in enumerate(nx.topological_generations(self._dag)):
            for node in nodes:
                self._dag.nodes[node]["layer"] = layer

    def _update_front_layer(self):
        """Update the front layer of the dag.

        Method works in-place.
        """
        self._front_layer = self._get_dag_layer(0)

    def _get_dag_layer(self, n_layer, qubits=False):
        """Return the :math:`n`-topological layer of the dag.

        Args:
            n_layer (int): Layer number.
            qubits (bool, optional): If ``True``, return the target qubits of the blocks in the layer.
                If ``False``, return the block numbers. Defaults to ``False``.

        Returns:
            (list): List of block numbers or target qubits.
        """

        if qubits:
            return [node[1]["qubits"] for node in self._dag.nodes(data=True) if node[1]["layer"] == n_layer]

        return [node[0] for node in self._dag.nodes(data="layer") if node[1] == n_layer]

    def _find_new_mapping(self):
        """Find the new best mapping by adding one swap."""
        candidates_evaluation = {}

        self._memory_map.append(self.circuit_map.physical_to_logical.copy())
        for candidate in self._swap_candidates():
            candidates_evaluation[candidate] = self._compute_cost(candidate)

        best_cost = min(candidates_evaluation.values())
        best_candidates = [key for key, value in candidates_evaluation.items() if value == best_cost]
        best_candidate = random.choice(best_candidates)

        for qubit in self.circuit_map.logical_pair_to_physical(best_candidate):
            self._delta_register[qubit] += self.delta
        self.circuit_map.update(best_candidate)
        self._temp_added_swaps.append(best_candidate)

    def _compute_cost(self, candidate: tuple):
        """Compute the cost associated to a possible SWAP candidate."""

        temporary_circuit = CircuitMap(temp=True)
        temporary_circuit.physical_to_logical = self.circuit_map.physical_to_logical
        temporary_circuit.update(candidate)

        if temporary_circuit.physical_to_logical in self._memory_map:
            return float("inf")

        tot_distance = 0.0
        weight = 1.0
        for layer in range(self.lookahead + 1):
            layer_gates = self._get_dag_layer(layer, qubits=True)
            avg_layer_distance = 0.0
            for lq_pair in layer_gates:
                qubits = temporary_circuit.logical_pair_to_physical(lq_pair)
                avg_layer_distance += (
                    max(self._delta_register[i] for i in qubits)
                    * (self._dist_matrix[qubits[0], qubits[1]] - 1.0)
                    / len(layer_gates)
                )
            tot_distance += weight * avg_layer_distance
            weight *= self.decay

        return tot_distance

    def _swap_candidates(self):
        """Returns a list of possible candidate SWAPs to be applied on logical qubits directly.

        The possible candidates are the ones sharing at least one qubit
        with a block in the front layer.

        Returns:
            (list): List of candidates.
        """
        candidates = []
        for block in self._front_layer:
            for qubit in self.circuit_map.get_physical_qubits(block):
                for connected in self.connectivity.neighbors(qubit):
                    candidate = tuple(
                        sorted(
                            (
                                self.circuit_map.physical_to_logical[qubit],
                                self.circuit_map.physical_to_logical[connected],
                            )
                        )
                    )
                    if candidate not in candidates:
                        candidates.append(candidate)

        return candidates

    def _check_execution(self):
        """Check if some blocks in the front layer can be executed in the current configuration.

        Returns:
            (list): Executable blocks if there are, ``None`` otherwise.
        """
        executable_blocks = []
        for block in self._front_layer:
            if (
                self.circuit_map.get_physical_qubits(block) in self.connectivity.edges
                or not self.circuit_map.circuit_blocks.search_by_index(block).entangled
            ):
                executable_blocks.append(block)

        if len(executable_blocks) == 0:
            return None

        return executable_blocks

    def _execute_blocks(self, blocklist: list):
        """Executes a list of blocks:
        -Remove the correspondent nodes from the dag and circuit representation.
        -Add the executed blocks to the routed circuit.
        -Update the dag layers and front layer.
        -Reset the mapping memory.

        Method works in-place.

        Args:
            blocklist (list): List of blocks.
        """
        for block_id in blocklist:
            block = self.circuit_map.circuit_blocks.search_by_index(block_id)
            self.circuit_map.execute_block(block)
            self._dag.remove_node(block_id)
        self._update_dag_layers()
        self._update_front_layer()
        self._memory_map = []
        self._delta_register = [1.0 for _ in self._delta_register]
        self._temp_added_swaps = []

    def _shortest_path_routing(self):
        """Route a gate in the front layer using the shortest path. This method is executed when the standard SABRE fails to find an optimized solution.

        Method works in-place.
        """

        min_distance = float("inf")
        shortest_path_qubits = None

        for block in self._front_layer:
            q1, q2 = self.circuit_map.get_physical_qubits(block)
            distance = self._dist_matrix[q1, q2]

            if distance < min_distance:
                min_distance = distance
                shortest_path_qubits = [q1, q2]

        shortest_path = nx.bidirectional_shortest_path(
            self.connectivity, shortest_path_qubits[0], shortest_path_qubits[1]
        )

        # move q1
        q1 = self.circuit_map.physical_to_logical[shortest_path[0]]
        for q2 in shortest_path[1:-1]:
            self.circuit_map.update((q1, self.circuit_map.physical_to_logical[q2]))


def _create_dag(gates_qubits_pairs: list) -> nx.DiGraph:
    """Helper method for :meth:`qibo.transpiler.router.Sabre`.

    Create direct acyclic graph (dag) of the circuit based on two qubit gates
    commutativity relations.

    Args:
        gates_qubits_pairs (list): List of qubits tuples where gates/blocks acts.

    Returns:
        (:class:`networkx.DiGraph`): Adjoint of the circuit.
    """
    dag = nx.DiGraph()
    dag.add_nodes_from(range(len(gates_qubits_pairs)))

    for i, _ in enumerate(gates_qubits_pairs):
        dag.nodes[i]["qubits"] = gates_qubits_pairs[i]

    # Find all successors
    connectivity_list = []
    for idx, gate in enumerate(gates_qubits_pairs):
        saturated_qubits = []
        for next_idx, next_gate in enumerate(gates_qubits_pairs[idx + 1 :]):
            for qubit in gate:
                if (qubit in next_gate) and (qubit not in saturated_qubits):
                    saturated_qubits.append(qubit)
                    connectivity_list.append((idx, next_idx + idx + 1))
            if len(saturated_qubits) >= 2:
                break
    dag.add_edges_from(connectivity_list)

    return _remove_redundant_connections(dag)


def _remove_redundant_connections(dag: nx.DiGraph) -> nx.DiGraph:
    """Helper method for :func:`qibo.transpiler.router._create_dag`.

    Remove redundant connection from a DAG using transitive reduction.

    Args:
        dag (:class:`networkx.DiGraph`): DAG to be reduced.

    Returns:
        (:class:`networkx.DiGraph`): Reduced DAG.
    """
    new_dag = nx.DiGraph()
    new_dag.add_nodes_from(dag.nodes(data=True))
    transitive_reduction = nx.transitive_reduction(dag)
    new_dag.add_edges_from(transitive_reduction.edges)

    return new_dag
