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
from qibo import Circuit, gates
from qibo.transpiler.optimizer import Preprocessing
from qibo.transpiler.pipeline import Passes
from qibo.transpiler.placer import Placer, ReverseTraversal, StarConnectivityPlacer
from qibo.transpiler.router import Router, Sabre, StarConnectivityRouter

from qililab.config import logger


class CircuitRouter:
    """Handles circuit routing, using a Placer and Router, and a coupling map. It has a single accessible method:

    - ``route(circuit: Circuit) -> tuple[Circuit, dict]``: Routes the virtual/logical qubits of a circuit, to the chip's physical qubits.

    Args:
        connectivity (nx.graph): Chip connectivity.
        placer (Placer | type[Placer] | tuple[type[Placer], dict], optional): `Placer` instance, or subclass `type[Placer]` to
            use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `ReverseTraversal`.
        router (Router | type[Router] | tuple[type[Router], dict], optional): `Router` instance, or subclass `type[Router]` to
            use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `Sabre`.
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

    def route(self, circuit: Circuit, iterations: int = 10) -> tuple[Circuit, dict]:
        """Routes the virtual/logical qubits of a circuit, to the chip's physical qubits.

        **Examples:**

        If we instantiate some ``Circuit``, ``Platform`` and ``CircuitTranspiler`` objects like:

        .. code-block:: python

            from qibo import gates
            from qibo.models import Circuit
            from qibo.transpiler.placer import ReverseTraversal, Trivial
            from qibo.transpiler.router import Sabre
            from qililab import build_platform
            from qililab.circuit_transpiler import CircuitTranspiler

            # Create circuit:
            c = Circuit(5)
            c.add(gates.CNOT(1, 0))

            # Create platform:
            platform = build_platform(runcard="<path_to_runcard>")
            coupling_map = platform.chip.get_topology()

            # Create transpiler:
            transpiler = CircuitTranspiler(platform)

        Now we can transpile like:

        .. code-block:: python

            # Default Transpilation:
            routed_circuit, final_layouts = transpiler.route_circuit([c])  # Defaults to ReverseTraversal, Sabre and platform connectivity

            # Non-Default Trivial placer, and coupling_map specified:
            routed_circuit, final_layouts = transpiler.route_circuit([c], placer=Trivial, router=Sabre, coupling_map)

            # Specifying one of the a kwargs:
            routed_circuit, final_layouts = transpiler.route_circuit([c], placer=Trivial, router=(Sabre, {"lookahead": 2}))

        Args:
            circuit (Circuit): circuit to route.
            iterations (int, optional): Number of times to repeat the routing pipeline, to keep the best stochastic result. Defaults to 10.

        Returns:
            Circuit: routed circuit.
            dict: final layout of the circuit.

        Raises:
            ValueError: If StarConnectivity Placer and Router are used with non-star topologies.
        """
        # Transpilation pipeline passes:
        routing_pipeline = Passes([self.preprocessing, self.placer, self.router], self.connectivity)
        # 1) Preprocessing adds qubits in the original circuit to match the number of qubits in the chip.
        # 2) Routing stage, where the final_layout and swaps will be created.
        # 3) Layout stage, where the initial_layout will be created.

        # Call the routing pipeline on the circuit, multiple times, and keep the best stochastic result:
        best_transp_circ, best_final_layout, least_swaps = self._iterate_routing(routing_pipeline, circuit, iterations)
        if least_swaps is not None:
            logger.info(f"The best found routing, has {least_swaps} swaps.")
        else:
            logger.info("No routing was done. Most probably due to routing iterations being 0.")

        return best_transp_circ, best_final_layout

    @staticmethod
    def _iterate_routing(routing_pipeline, circuit: Circuit, iterations: int = 10) -> tuple[Circuit, dict, int | None]:
        """Iterates the routing pipeline, to keep the best stochastic result.

        Args:
            routing_pipeline (Passes): Transpilation pipeline passes.
            circuit (Circuit): Circuit to route.
            iterations (int, optional): Number of times to repeat the routing pipeline, to keep the best stochastic result. Defaults to 10.

        Returns:
            tuple[Circuit, dict, int]: Best transpiled circuit, best final layout and least swaps.
        """
        # We repeat the routing pipeline a few times, to keep the best stochastic result:
        least_swaps: int | None = None
        for _ in range(iterations):
            # Call the routing pipeline on the circuit:
            transpiled_circ, final_layout = routing_pipeline(circuit)

            # Get the number of swaps in the circuits:
            n_swaps = len(transpiled_circ.gates_of_type(gates.SWAP))

            # Checking which is the best transpilation:
            if least_swaps is None or n_swaps < least_swaps:
                least_swaps = n_swaps
                best_transpiled_circ, best_final_layout = transpiled_circ, final_layout

            # If a mapping needs no swaps, we are finished:
            if n_swaps == 0:
                break

        return best_transpiled_circ, best_final_layout, least_swaps

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
            return Sabre(connectivity)

        kwargs = {}
        if isinstance(router, tuple):
            router, kwargs = router

        # If the router is already an instance, we update the connectivity to the platform one:
        if isinstance(router, Router):
            if kwargs:
                logger.warning("Ignoring router kwargs, as the router is already an instance.")
            router.connectivity = connectivity
            logger.warning("Substituting the router connectivity by the platform one.")
            return router

        # If the router is a Router subclass, we instantiate it:
        with contextlib.suppress(TypeError, ValueError):
            if issubclass(router, Router):
                return router(connectivity, **kwargs)

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
            return ReverseTraversal(connectivity, router)

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
            logger.warning("Substituting the placer connectivity by the platform one.")
            return placer

        # If the placer is a Placer subclass, we instantiate it:
        with contextlib.suppress(TypeError, ValueError):
            if issubclass(placer, Placer):
                return placer(connectivity, **kwargs)

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
            tuple[Placer | type[Placer], dict]: Tuple containing the final placer and its kwargs
        """
        # If the placer is a ReverseTraversal instance, we update the connectivity to the platform one:
        if isinstance(placer, ReverseTraversal):
            placer.routing_algorithm.connectivity = connectivity
            logger.warning("Substituting the ReverseTraversal router connectivity, by the platform one.")
            return placer, kwargs

        # Else is placer is not an instance, we need to check the routing algorithm:

        # If no routing algorithm is passed, we use the Transpilation Router, for the ReverseTraversal too:
        if "routing_algorithm" not in kwargs:
            kwargs["routing_algorithm"] = router
            return placer, kwargs

        # If the routing algorithm is a Router instance, we update the connectivity to the platform one:
        if isinstance(kwargs["routing_algorithm"], Router):
            logger.warning(
                "Substituting the passed connectivity for the ReverseTraversal routing algorithm, by the platform connectivity",
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
