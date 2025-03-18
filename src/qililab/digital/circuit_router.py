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

"""CircuitRouter class"""

import contextlib

import networkx as nx
import numpy as np
from qibo import Circuit, gates
from qibo.transpiler.optimizer import Preprocessing
from qibo.transpiler.pipeline import Passes
from qibo.transpiler.placer import Placer, ReverseTraversal, StarConnectivityPlacer
from qibo.transpiler.router import Router, Sabre, StarConnectivityRouter

from qililab.config import logger
from qililab.digital.circuit_optimizer import CircuitOptimizer
from qililab.digital.native_gates import _GateHandler


class CircuitRouter:
    """Handles circuit routing, using a Placer and Router, and a coupling map. It has a single accessible method:

    - ``route(circuit: Circuit) -> tuple[Circuit, dict]``: Routes the virtual/logical qubits of a circuit, to the chip's physical qubits.

    Args:
        connectivity (nx.graph): Chip connectivity.
        placer (Placer | type[Placer] | tuple[type[Placer], dict], optional): ``Placer`` instance, or subclass ``type[Placer]`` to
            use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to ``ReverseTraversal``.
        router (Router | type[Router] | tuple[type[Router], dict], optional): ``Router`` instance, or subclass ``type[Router]`` to
            use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to ``Sabre``.
    """

    def __init__(
        self,
        connectivity: nx.graph,
        placer: Placer | type[Placer] | tuple[type[Placer], dict] | None = None,
        router: Router | type[Router] | tuple[type[Router], dict] | None = None,
    ):
        self.connectivity = connectivity
        """nx.graph: Chip connectivity."""

        self.preprocessing = Preprocessing(self.connectivity)
        """Preprocessing: Stage to add qubits in the original circuit to match the number of qubits in the chip."""

        self.router = self._build_router(router, self.connectivity)
        """Router: Routing stage, where the final_layout and swaps will be created. Defaults to Sabre."""

        self.placer = self._build_placer(placer, self.router, self.connectivity)
        """Placer: Layout stage, where the initial_layout will be created. Defaults to ReverseTraversal."""

        # Cannot use Star algorithms for non star-connectivities:
        if self._if_star_algorithms_for_nonstar_connectivity(self.connectivity, self.placer, self.router):
            raise (ValueError("StarConnectivity Placer and Router can only be used with star topologies"))

        # Transpilation pipeline passes:
        self.pipeline = Passes([self.preprocessing, self.placer, self.router], self.connectivity)
        """Routing pipeline passes: Preprocessing, Placer and Router passes. Defaults to Passes([Preprocessing, ReverseTraversal, Sabre])."""
        # 1) Preprocessing adds qubits in the original circuit to match the number of qubits in the chip.
        # 2) Routing stage, where the final_layout and swaps will be created.
        # 3) Layout stage, where the initial_layout will be created.

    def route(self, circuit: Circuit, iterations: int = 10) -> tuple[Circuit, list[int]]:
        """Routes the virtual/logical qubits of a circuit to the physical qubits of a chip. Returns and logs the final qubit layout.

        Check public docstring in :meth:`.CircuitTranspiler.route_circuit()` for more information.

        Args:
            circuit (Circuit): circuit to route.
            iterations (int, optional): Number of times to repeat the routing pipeline, to keep the best stochastic result. Defaults to 10.

        Returns:
            tuple [Circuit, list[int]: Routed circuit and its corresponding final layout (Initial Re-mapping + SWAPs routing) of
                the Original Logical Qubits (l_q) in the physical circuit (wires): [l_q in wire 0, l_q in wire 1, ...].

        Raises:
            ValueError: If StarConnectivity Placer and Router are used with non-star topologies.
            ValueError: If the final layout is not valid, i.e. a qubit is mapped to more than one physical qubit.
        """
        # Call the routing pipeline on the circuit, multiple times, and keep the best stochastic result:
        best_transp_circ, least_swaps, best_final_layout = self._iterate_routing(self.pipeline, circuit, iterations)

        if least_swaps is not None:
            logger.info(f"The best found routing, has {least_swaps} swaps.")
            logger.info(
                f"{best_transp_circ.wire_names}: Initial Re-mapping of the Original Logical Qubits (l_q), in the Physical Circuit: [l_q in wire 0, l_q in wire 1, ...]."
            )
            logger.info(
                f"{best_final_layout}: Final Re-mapping (Initial + SWAPs routing) of the Original Logical Qubits (l_q), in the Physical Circuit: [l_q in wire 0, l_q in wire 1, ...]."
            )
        else:
            logger.info("No routing was done. Most probably due to routing iterations being 0.")

        return best_transp_circ, best_final_layout

    @staticmethod
    def _iterate_routing(
        routing_pipeline: Passes, circuit: Circuit, iterations: int = 10
    ) -> tuple[Circuit, int | None, list[int]]:
        """Iterates through the routing pipeline to retain the best stochastic result. Returns and/or logs the final qubit layout.

        Args:
            routing_pipeline (Passes): Transpilation pipeline passes.
            circuit (Circuit): Circuit to route.
            iterations (int, optional): Number of times to repeat the routing pipeline, to keep the best stochastic result. Defaults to 10.

        Returns:
            tuple[Circuit, int | None, list[int]]: Best routed circuit, least number of swaps required, and the corresponding best final
                layout of the original logical qubits in the physical circuit: [Logical qubit in wire 1, Logical qubit in wire 2, ...].
        """
        # We repeat the routing pipeline a few times, to keep the best stochastic result:
        least_swaps: int | None = None
        for _ in range(iterations):
            # Call the routing pipeline on the circuit:
            transpiled_circ, final_layout = routing_pipeline(circuit)

            # Undo the initial remapping (wire_names), for executing in correct chips:
            transpiled_circ = CircuitRouter._apply_initial_remap(transpiled_circ)

            # Remove redundant swaps at the start of the transpiled circuit:
            transpiled_circ = CircuitOptimizer.remove_redundant_start_controlled_gates(transpiled_circ, gates.SWAP)

            # Get the number of swaps in the circuits:
            n_swaps = len(transpiled_circ.gates_of_type(gates.SWAP))

            # Checking which is the best transpilation:
            if least_swaps is None or n_swaps < least_swaps:
                least_swaps = n_swaps
                best_transpiled_circ, best_final_layout = transpiled_circ, final_layout

            # If a mapping needs no swaps, we are finished:
            if n_swaps == 0:
                break

        best_final_layout = CircuitRouter._get_logical_qubit_of_each_wire(best_final_layout)

        return best_transpiled_circ, least_swaps, best_final_layout

    @staticmethod
    def _apply_initial_remap(transpiled_circ: Circuit) -> Circuit:
        """Applies the initial remapping of the circuit (wire_names), to the qubits of all gates, so we can execute in the connected qubits.

        Args:
            transpiled_circ (Circuit): Circuit with the initial remapping.

        Returns:
            Circuit: Circuit with the initial remapping applied to the gate qubits.
        """
        new_queue = []
        for gate in transpiled_circ.queue:
            qubits = [transpiled_circ.wire_names.index(qubit) for qubit in gate.qubits]
            gate = _GateHandler.create_gate(type(gate).__name__, qubits, gate.init_kwargs)
            new_queue.append(gate)

        return _GateHandler.create_circuit_from_gates(new_queue, transpiled_circ.nqubits, transpiled_circ.wire_names)

    @staticmethod
    def _get_logical_qubit_of_each_wire(final_layout: dict[int, int]) -> list[int]:
        """Transforms Qibo's format for the final_layout into a permutation in a list.

        Args:
            final_layout (dict[int, int]): Qibo's final layout (Initial Re-mapping + SWAPs routing) of the
                Original Logical Qubits (l_q) in the physical circuit (wire): {l_q: wire where it ended for execution}.

        Returns:
            final_layout (list[int]): Final layout (Initial Re-mapping + SWAPs routing) of the Original Logical Qubits (l_q) in the Physical Circuit (wire), in a list.
                Each index is a physical qubit (wire), and its value the corresponding Original Logical Qubit (l_q) state its containing: [l_q in wire 0, l_q in wire 1, ...].
        """
        if CircuitRouter._if_layout_is_not_valid(final_layout):
            raise ValueError(
                f"The final layout: {final_layout} is not valid. i.e. a logical qubit is mapped to more than one physical qubit, or a key/value isn't a number. Try again, if the problem persists, try another placer/routing algorithm."
            )
        return [logical_q for logical_q, _ in sorted(final_layout.items(), key=lambda q_wire_in_1: q_wire_in_1[1])]

    @staticmethod
    def _if_star_algorithms_for_nonstar_connectivity(connectivity: nx.Graph, placer: Placer, router: Router) -> bool:
        """True if the StarConnectivity Placer or Router are being used without a star connectivity.

        Args:
            connectivity (nx.Graph): Chip connectivity.
            placer (Placer): Placer instance.
            router (Router): Router instance.

        Returns:
            bool: True if the StarConnectivity Placer or Router are being used without a star connectivity.
        """

        return not nx.is_isomorphic(connectivity, nx.star_graph(4)) and (
            isinstance(placer, StarConnectivityPlacer) or isinstance(router, StarConnectivityRouter)
        )

    @staticmethod
    def _highest_degree_node(connectivity: nx.Graph) -> int:
        """Returns the node with the highest degree in the connectivity graph.

        Args:
            connectivity (nx.Graph): Chip connectivity.

        Returns:
            int: Node with the highest degree in the connectivity graph.
        """
        return max(dict(connectivity.degree()).items(), key=lambda x: x[1])[0]

    @staticmethod
    def _if_layout_is_not_valid(layout: dict[int, int]) -> bool:
        """True if the layout is not valid.

        For example, if a qubit is mapped to more than one physical qubit. Or if the keys or values are not int.

        Args:
            layout (dict[int, int]): Final layout of the circuit.

        Returns:
            bool: True if the layout is not valid.
        """
        return (
            len(layout.values()) != len(set(layout.values()))
            or len(layout.keys()) != len(set(layout.keys()))
            or not all(np.issubdtype(type(value), np.integer) for value in layout.values())
            or not all(np.issubdtype(type(keys), np.integer) for keys in layout)
        )

    @staticmethod
    def _build_router(router: Router | type[Router] | tuple[type[Router], dict], connectivity: nx.Graph) -> Router:
        """Build a `Router` instance, given the pass router in whatever format and the connectivity graph.

        Args:
            router (Router | type[Router] | tuple[type[Router], dict]): Router instance, subclass or tuple(subclass, kwargs).
            connectivity (nx.Graph): Chip connectivity.

        Returns:
            Router: Router instance.

        Raises:
            ValueError: If the router is not a Router subclass or instance.
        """
        # If router is None, we build default one:
        if router is None:
            return Sabre(connectivity=connectivity)

        kwargs = {}
        if isinstance(router, tuple):
            router, kwargs = router

        # If the router is already an instance, we update the connectivity to the platform one:
        if isinstance(router, Router):
            if kwargs:
                logger.warning("Ignoring router kwargs, as the router is already an instance.")
            router.connectivity = connectivity
            logger.warning("Substituting the router connectivity by the transpiler/platform/coupling_map one.")
            return router

        # If the router is a Router subclass, we instantiate it:
        with contextlib.suppress(TypeError, ValueError):
            if issubclass(router, Router):
                return router(connectivity=connectivity, **kwargs)

        raise TypeError(
            f"`router` arg ({type(router)}), must be a `Router` instance, subclass or tuple(subclass, kwargs), in `execute()`, `compile()`, `transpile_circuit()` or `route_circuit()`."
        )

    def _build_placer(
        self, placer: Placer | type[Placer] | tuple[type[Placer], dict], router: Router, connectivity: nx.graph
    ) -> Placer:
        """Build a `Placer` instance, given the pass router in whatever format and the connectivity graph.

        Args:
            router (Placer | type[Placer] | tuple[type[Placer], dict]): Placer instance, subclass or tuple(subclass, kwargs).
            connectivity (nx.Graph): Chip connectivity.

        Returns:
            Placer: Placer instance.

        Raises:
            ValueError: If the router is not a Placer subclass or instance.
        """
        # If placer is None, we build default one:
        if placer is None:
            return ReverseTraversal(connectivity=connectivity, routing_algorithm=router)

        kwargs = {}
        if isinstance(placer, tuple):
            placer, kwargs = placer

        # For ReverseTraversal placer, we need to check the routing algorithm has correct connectivity:
        if placer == ReverseTraversal or isinstance(placer, ReverseTraversal):
            placer, kwargs = self._check_ReverseTraversal_routing_connectivity(placer, kwargs, connectivity, router)

        # If the placer is already an instance, we update the connectivity to the platform one:
        if isinstance(placer, Placer):
            if kwargs:
                logger.warning("Ignoring placer kwargs, as the placer is already an instance.")
            placer.connectivity = connectivity
            logger.warning("Substituting the placer connectivity by the transpiler/platform/coupling_map one.")
            return placer

        # If the placer is a Placer subclass, we instantiate it:
        with contextlib.suppress(TypeError, ValueError):
            if issubclass(placer, Placer):
                return placer(connectivity=connectivity, **kwargs)

        raise TypeError(
            f"`placer` arg ({type(placer)}), must be a `Placer` instance, subclass or tuple(subclass, kwargs), in `execute()`, `compile()`, `transpile_circuit()` or `route_circuit()`."
        )

    @staticmethod
    def _check_ReverseTraversal_routing_connectivity(
        placer: Placer | type[Placer], kwargs: dict, connectivity: nx.Graph, router: Router
    ) -> tuple[Placer | type[Placer], dict]:
        """Checks if the kwargs are valid for the Router subclass, of the ReverseTraversal Placer.

        Args:
            placer (Placer | type[Placer])
            placer_kwargs (dict): kwargs for the Placer subclass.
            connectivity (nx.Graph): Chip connectivity.
            router (Router): Original transpilation Router subclass.

        Raises:
            ValueError: If the routing_algorithm is not a Router subclass or instance.

        Returns:
            tuple[Placer | type[Placer], dict]: tuple containing the final placer and its kwargs
        """
        # If the placer is a ReverseTraversal instance, we update the connectivity to the platform one:
        if isinstance(placer, ReverseTraversal):
            placer.routing_algorithm.connectivity = connectivity
            logger.warning(
                "Substituting the ReverseTraversal router connectivity, by the transpiler/platform/coupling_map one."
            )
            return placer, kwargs

        # Else is placer is not an instance, we need to check the routing algorithm:

        # If no routing algorithm is passed, we use the Transpilation Router, for the ReverseTraversal too:
        if "routing_algorithm" not in kwargs:
            kwargs["routing_algorithm"] = router
            return placer, kwargs

        # If the routing algorithm is a Router instance, we update the connectivity to the platform one:
        if isinstance(kwargs["routing_algorithm"], Router):
            logger.warning(
                "Substituting the passed connectivity for the routing algorithm, by the platform/transpiler/coupling_map connectivity",
            )
            kwargs["routing_algorithm"].connectivity = connectivity
            return placer, kwargs

        # If the routing algorithm is a Router subclass, we instantiate it, with the platform connectivity:
        with contextlib.suppress(TypeError, ValueError):
            if issubclass(kwargs["routing_algorithm"], Router):
                kwargs["routing_algorithm"] = kwargs["routing_algorithm"](connectivity)
                return placer, kwargs

        # If the routing algorithm is not a Router subclass or instance, we raise an error:
        raise TypeError(
            f"`routing_algorithm` `Placer` kwarg ({kwargs['routing_algorithm']}) must be a `Router` subclass or instance, in `execute()`, `compile()`, `transpile_circuit()` or `route_circuit()`."
        )
