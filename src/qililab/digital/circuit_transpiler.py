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

"""Circuit Transpiler class"""

import networkx as nx
from qibo.models import Circuit
from qibo.transpiler.placer import Placer
from qibo.transpiler.router import Router

from qililab.config import logger
from qililab.digital.circuit_optimizer import CircuitOptimizer
from qililab.digital.circuit_router import CircuitRouter
from qililab.digital.circuit_to_pulses import CircuitToPulses
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings

from .gate_decompositions import translate_gates


class CircuitTranspiler:
    """Handles circuit transpilation. It has 3 accessible methods:

    - ``circuit_to_native``: transpiles a qibo circuit to native gates (Drag, CZ, Wait, M) and optionally RZ if optimize=False (optimize=True by default)
    - ``circuit_to_pulses``: transpiles a native gate circuit to a `PulseSchedule`
    - ``transpile_circuit``: runs both of the methods above sequentially

    Args:
        platform (Platform): platform object containing the runcard and the chip's physical qubits.
    """

    def __init__(self, digital_compilation_settings: DigitalCompilationSettings):  # type: ignore # ignore typing to avoid importing platform and causing circular imports
        self.digital_compilation_settings = digital_compilation_settings

    def transpile_circuits(
        self,
        circuits: list[Circuit],
        placer: Placer | type[Placer] | tuple[type[Placer], dict] | None = None,
        router: Router | type[Router] | tuple[type[Router], dict] | None = None,
        routing_iterations: int = 10,
        optimize: bool = True,
    ) -> tuple[list[PulseSchedule], list[dict]]:
        """Transpiles a list of ``qibo.models.Circuit`` objects into a list of pulse schedules.

        The process involves the following steps:

        1. Routing and Placement: Routes and places the circuit's logical qubits onto the chip's physical qubits. The final qubit layout is returned and logged. This step uses the `placer`, `router`, and `routing_iterations` parameters if provided; otherwise, default values are applied.
        2. Native Gate Translation: Translates the circuit into the chip's native gate set (CZ, RZ, Drag, Wait, and M (Measurement)).
        3. Pulse Schedule Conversion: Converts the native gate circuit into a pulse schedule using calibrated settings from the runcard.

        |

        If `optimize=True` (default behavior), the following optimizations are also performed:

        - Canceling adjacent pairs of Hermitian gates (H, X, Y, Z, CNOT, CZ, and SWAPs).
        - Applying virtual Z gates and phase corrections by combining multiple pulses into a single one and commuting them with virtual Z gates.

        |

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

            # Create transpiler:
            transpiler = CircuitTranspiler(platform)

        Now we can transpile like, in the following examples:

        .. code-block:: python

            # Default Transpilation (with ReverseTraversal, Sabre, platform's connectivity and optimize = True):
            routed_circuit, final_layouts = transpiler.transpile_circuits([c])

            # Or another case, not doing optimization for some reason, and with Non-Default placer and router:
            routed_circuit, final_layout = transpiler.transpile_circuits([c], placer=Trivial, router=Sabre, optimize=False)

            # Or also specifying the `router` with kwargs:
            routed_circuit, final_layouts = transpiler.transpile_circuits([c], router=(Sabre, {"lookahead": 2}))

        Args:
            circuits (list[Circuit]): list of qibo circuits.
            placer (Placer | type[Placer] | tuple[type[Placer], dict], optional): `Placer` instance, or subclass `type[Placer]` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `ReverseTraversal`.
            router (Router | type[Router] | tuple[type[Router], dict], optional): `Router` instance, or subclass `type[Router]` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `Sabre`.
            routing_iterations (int, optional): Number of times to repeat the routing pipeline, to get the best stochastic result. Defaults to 10.
            optimize (bool, optional): whether to optimize the circuit and/or transpilation. Defaults to True.

        Returns:
            tuple[list[PulseSchedule],list[dict[str, int]]]: list of pulse schedules and list of the final layouts of the qubits, in each circuit {"qI": J}.
        """

        # Routing stage;
        routed_circuits, final_layouts = zip(
            *(self.route_circuit(circuit, placer, router, iterations=routing_iterations) for circuit in circuits)
        )
        logger.info(f"Circuits final layouts: {final_layouts}")

        # Optimze qibo gates, cancellating redundant gates, stage:
        if optimize:
            routed_circuits = tuple(self.optimize_circuit(circuit) for circuit in routed_circuits)

        # Unroll to Natives stage:
        native_circuits = (self.circuit_to_native(circuit) for circuit in routed_circuits)

        # Optimize native gates, optimize transpilation stage:
        if optimize:
            native_circuits = (self.optimize_transpilation(circuit) for circuit in native_circuits)

        # Pulse schedule stage:
        pulse_schedules = self.circuit_to_pulses(list(native_circuits))

        return pulse_schedules, list(final_layouts)

    def route_circuit(
        self,
        circuit: Circuit,
        placer: Placer | type[Placer] | tuple[type[Placer], dict] | None = None,
        router: Router | type[Router] | tuple[type[Router], dict] | None = None,
        coupling_map: list[tuple[int, int]] | None = None,
        iterations: int = 10,
    ) -> tuple[Circuit, dict[str, int]]:
        """Routes the virtual/logical qubits of a circuit to the physical qubits of a chip. Returns and logs the final qubit layout.

        This process uses the provided `placer`, `router`, and `routing_iterations` parameters if they are passed; otherwise, default values are applied.

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
            coupling_map = platform.digital_compilation_settings.topology

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
            coupling_map (list[tuple[int, int]], optional): coupling map of the chip to route. This topology will be the one that rules,
                which will overwrite any other in an instance of router or placer. Defaults to the platform topology.
            placer (Placer | type[Placer] | tuple[type[Placer], dict], optional): `Placer` instance, or subclass `type[Placer]` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `ReverseTraversal`.
            router (Router | type[Router] | tuple[type[Router], dict], optional): `Router` instance, or subclass `type[Router]` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `Sabre`.
            iterations (int, optional): Number of times to repeat the routing pipeline, to keep the best stochastic result. Defaults to 10.


        Returns:
            tuple[Circuit, dict[str, int]]: routed circuit, and final layout of the circuit {"qI": J}.

        Raises:
            ValueError: If StarConnectivity Placer and Router are used with non-star topologies.
        """
        # Get the chip's connectivity
        topology = nx.Graph(coupling_map if coupling_map is not None else self.digital_compilation_settings.topology)

        circuit_router = CircuitRouter(topology, placer, router)

        return circuit_router.route(circuit, iterations)

    def optimize_circuit(self, circuit: Circuit) -> Circuit:
        """Main function to optimize circuits with. Currently works by cancelling adjacent hermitian gates.

        The total optimization can/might be expanded in the future.

        Args:
            circuit (Circuit): circuit to optimize.

        Returns:
            Circuit: optimized circuit.
        """
        return CircuitOptimizer.run_gate_cancellations(circuit)

    def circuit_to_native(self, circuit: Circuit) -> Circuit:
        """Converts circuit with qibo gates to circuit with native gates (CZ, RZ, Drag, Wait and M (Measurement).

        Args:
            circuit (Circuit): circuit with qibo gate.

        Returns:
            new_circuit (Circuit): circuit with transpiled gates
        """
        new_circuit = Circuit(circuit.nqubits)
        new_circuit.add(translate_gates(circuit.queue))

        return new_circuit

    def optimize_transpilation(self, circuit: Circuit) -> Circuit:
        """Optimizes transpiled circuit by applying virtual Z gates.

        This is done by moving all RZ to the left of all operators as a single RZ. The corresponding cumulative rotation
        from each RZ is carried on as phase in all drag pulses left of the RZ operator.

        Virtual Z gates are also applied to correct phase errors from CZ gates.

        The final RZ operator left to be applied as the last operator in the circuit can afterwards be removed since the last
        operation is going to be a measurement, which is performed on the Z basis and is therefore invariant under rotations
        around the Z axis.

        This last step can also be seen from the fact that an RZ operator applied on a single qubit, with no operations carried
        on afterwards induces a phase rotation. Since phase is an imaginary unitary component, its absolute value will be 1
        independent on any (unitary) operations carried on it.

        Mind that moving an operator to the left is equivalent to applying this operator last so
        it is actually moved to the _right_ of ``Circuit.queue`` (last element of list).

        For more information on virtual Z gates, see https://arxiv.org/abs/1612.00858

        Args:
            circuit (Circuit): circuit with native gates, to optimize.

        Returns:
            Circuit: Circuit with optimized transpiled gates.
        """
        optimizer = CircuitOptimizer(self.digital_compilation_settings)

        output_circuit = Circuit(circuit.nqubits)
        output_circuit.add(optimizer.optimize_transpilation(circuit))
        return output_circuit

    def circuit_to_pulses(self, circuits: list[Circuit]) -> list[PulseSchedule]:
        """Translates a list of circuits into a list of pulse sequences (each circuit to an independent pulse sequence).

        For each circuit gate we look up for its corresponding gates settings in the runcard (the name of the class of the circuit
        gate and the name of the gate in the runcard should match) and load its schedule of GateEvents.

        Each gate event corresponds to a concrete pulse applied at a certain time w.r.t the gate's start time and through a specific bus
        (see gates settings docstrings for more details).

        Measurement gates are handled in a slightly different manner. For a circuit gate M(0,1,2) the settings for each M(0), M(1), M(2)
        will be looked up and will be applied in sync. Note that thus a circuit gate for M(0,1,2) is different from the circuit sequence
        M(0)M(1)M(2) since the later will not be necessarily applied at the same time for all the qubits involved.

        Times for each qubit are kept track of with the dictionary `time`.

        The times at which each pulse is applied are padded if they are not multiples of the minimum clock time. This means that if min clock
        time is 4 and a pulse applied to qubit k lasts 17ns, the next pulse at qubit k will be at t=20ns

        Args:
            circuits (List[Circuit]): List of Qibo Circuit classes.

        Returns:
            list[PulseSequences]: List of :class:`PulseSequences` classes.
        """
        circuit_to_pulses = CircuitToPulses(self.digital_compilation_settings)
        return [circuit_to_pulses.run(circuit) for circuit in circuits]
