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

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import networkx as nx
from qibo.gates import SWAP, M

from qililab.digital.circuit_optimizer import CircuitOptimizer
from qililab.digital.circuit_router import CircuitRouter
from qililab.digital.circuit_to_pulses import CircuitToPulses

from .gate_decompositions import translate_gates

if TYPE_CHECKING:
    from qibo import Circuit, gates
    from qibo.transpiler.placer import Placer
    from qibo.transpiler.router import Router

    from qililab.pulse.pulse_schedule import PulseSchedule
    from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings


@dataclass
class DigitalTranspilationConfig:
    """Dataclass containing the digital transpilation configuration. Used in the :meth:`.CircuitTranspiler.transpile_circuit()` method"""

    routing: bool = False  # TODO: Change to True, when user confirms it works well.
    """(bool, optional): Whether to route the circuit. Currently this only works if no SWAP gate is after a Measurement for each qubit. Defaults to False."""

    placer: Placer | type[Placer] | tuple[type[Placer], dict] | None = None
    """(Placer | type[Placer] | tuple[type[Placer], dict], optional): ``Placer`` instance, or subclass ``type[Placer]`` to
        use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to ``ReverseTraversal``."""

    router: Router | type[Router] | tuple[type[Router], dict] | None = None
    """(Router | type[Router] | tuple[type[Router], dict], optional): ``Router`` instance, or subclass ``type[Router]`` to
        use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to ``Sabre``."""

    routing_iterations: int = 10
    """(int, optional): Number of times to repeat the routing pipeline, to get the best stochastic result. Defaults to 10."""

    optimize: bool = False  # TODO: Maybe also change to True, when user confirms it works well.
    """(bool, optional): Whether to optimize the circuit and/or transpilation. Defaults to False."""

    @property
    def _attributes_ordered(self) -> tuple:
        """Returns the attributes of the dataclass in order, as a tuple."""
        return self.routing, self.placer, self.router, self.routing_iterations, self.optimize


class CircuitTranspiler:
    """Handles circuit transpilation (routing, optimization, native gate translation, and pulse scheduling).

    Its main method, which sequentially calls the rest, is: :meth:`.transpile_circuit()`.

    Args:
        settings (DigitalCompilationSettings): Object containing the Digital Compilations Settings and the info on chip's physical qubits.
            It can be obtained from the :attr:`.Platform.digital_compilation_settings` attribute.
    """

    def __init__(self, settings: DigitalCompilationSettings):
        self.settings: DigitalCompilationSettings = settings
        """Object containing the digital compilations settings and the info on chip's physical qubits."""

        self.optimizer: CircuitOptimizer = CircuitOptimizer(self.settings)
        """Object to do do the complex circuit manipulations with."""

    def transpile_circuit(
        self,
        circuit: Circuit,
        transpilation_config: DigitalTranspilationConfig | None = None,
    ) -> tuple[PulseSchedule, list[int] | None]:
        """Transpiles a list of ``qibo.models.Circuit`` objects into a list of pulse schedules.

        The process involves the following steps (by default only: **3.**, **4**., and **6.** run):


        1. **Routing and Placement:** Routes and places the circuit's logical qubits onto the chip's physical qubits. The final qubit layout is returned and logged. This step uses the ``placer``, ``router``, and ``routing_iterations`` parameters if provided; otherwise, default values are applied. Refer to the :meth:`.CircuitTranspiler.route_circuit()` method for more information.

        2. **1st Optimization:** Canceling adjacent pairs of Hermitian gates (H, X, Y, Z, CNOT, CZ, and SWAPs). Refer to the :meth:`.CircuitTranspiler.optimize_gates()` method for more information.

        3. **Native Gate Translation:** Translates the circuit into the chip's native gate set (CZ, RZ, Drag, Wait, and M (Measurement)). Refer to the :meth:`.CircuitTranspiler.gates_to_native()` method for more information.

        4. **Adding phases to our Drag gates:** commuting RZ gates until the end of the circuit to discard them as virtual Z gates, and due to the phase corrections from CZ. Refer to the :meth:`.CircuitTranspiler.add_phases_from_RZs_and_CZs_to_drags()` method for more information.

        5. **2nd Optimization:** Optimizing the resulting Drag gates, by combining multiple pulses into a single one. Refer to the :meth:`.CircuitTranspiler.optimize_transpiled_gates()` method for more information.

        6. **Pulse Schedule Conversion:** Converts the native gates into a pulse schedule using calibrated settings from the runcard. Refer to the :meth:`.CircuitTranspiler.gates_to_pulses()` method for more information.

        .. note::

            Default steps are only: **3.**, **4**., and **6.**, since they are always needed.

            To do Step **1.** set ``routing=True`` (default behavior skips it).

            To do Steps **2.** and **5.** set ``optimize=True`` (default behavior skips it).

        .. note::

            If the circuit has SWAP gates after a Measurement gate, the automatic routing will not work, better to use the :meth:`.CircuitRouter.route()` method manually, and track the mapping of measurement results before execution.

        **Examples:**

        If we instantiate some ``Circuit``, ``Platform`` and ``CircuitTranspiler`` objects like:

        .. code-block:: python

            from qibo import gates
            from qibo.models import Circuit
            from qibo.transpiler.placer import ReverseTraversal, Random
            from qibo.transpiler.router import Sabre
            from qililab import build_platform
            from qililab.digital import CircuitTranspiler

            # Create circuit:
            c = Circuit(5)
            c.add(gates.CNOT(1, 0))

            # Create platform:
            platform = build_platform(runcard="<path_to_runcard>")

            # Create transpiler:
            transpiler = CircuitTranspiler(platform.digital_compilation_settings)

        Now we can transpile like, in the following examples:

        .. code-block:: python

            # Default Transpilation (with ReverseTraversal, Sabre, platform's connectivity and optimize = True):
            transpiled_circuit, final_layouts = transpiler.transpile_circuit(c)

            # Or another case, not doing optimization for some reason, and with Non-Default placer:
            transpilation_settings = DigitalTranspilationConfig(placer=Random, optimize=False)
            transpiled_circuit, final_layout = transpiler.transpile_circuit(c, transpilation_config=transpilation_settings)

            # Or also specifying the `router` with kwargs:
            transpilation_settings = DigitalTranspilationConfig(router=(Sabre, {"lookahead": 2}))
            transpiled_circuit, final_layouts = transpiler.transpile_circuit(c, transpilation_config=transpilation_settings)

        .. note::

            Check :ref:`Transpilation <transpilation>`, for more examples of how ``execute()``'s methods automatically apply this.

        Args:
            circuit (Circuit): Qibo circuit.
            transpilation_config (DigitalTranspilationConfig, optional): :class:`.DigitalTranspilationConfig` dataclass containing
                the configuration used during transpilation. Defaults to ``None`` (not changing any default value).
                Check the class:`.DigitalTranspilationConfig` documentation for the keys and values it can contain.

        Returns:
            tuple[PulseSchedule, list[int] | None]: Pulse schedule and its corresponding final layout (Initial Re-mapping + SWAPs routing) of
                the Original Logical Qubits (l_q) in the physical circuit (wires): [l_q in wire 0, l_q in wire 1, ...] (None = trivial mapping).
        """
        # Default values:
        if transpilation_config is None:
            transpilation_config = DigitalTranspilationConfig()

        # Unpack dataclass attributes:
        routing, placer, router, routing_iterations, optimize = transpilation_config._attributes_ordered

        # Routing stage;
        if routing:
            # Check that no gate is after a M gate in each qubit of the circuit, else automatic un-reordering will not work.
            CircuitTranspiler._check_that_no_SWAP_gate_is_after_measurement(circuit, before_or_after="before")
            circuit_gates, nqubits, final_layout = self.route_circuit(circuit, placer, router, routing_iterations)
            CircuitTranspiler._check_that_no_SWAP_gate_is_after_measurement(circuit, before_or_after="after")
            # Check again, after routing, so no SWAP gate has appeared behind a measurement gate.
        else:
            circuit_gates, nqubits = circuit.queue, circuit.nqubits
            final_layout = None  # Random mapping

        # Optimze qibo gates, cancelling redundant gates:
        if optimize:
            circuit_gates = self.optimize_gates(circuit_gates)

        # Unroll to Natives gates:
        circuit_gates = self.gates_to_native(circuit_gates)

        # Add phases from RZs and CZs to Drags:
        circuit_gates = self.add_phases_from_RZs_and_CZs_to_drags(circuit_gates, nqubits)

        # Optimze transpiled qibo gates, cancelling redundant gates:
        if optimize:
            circuit_gates = self.optimize_transpiled_gates(circuit_gates)

        # Pulse schedule stage:
        pulse_schedule = self.gates_to_pulses(circuit_gates)

        return pulse_schedule, final_layout

    def route_circuit(
        self,
        circuit: Circuit,
        placer: Placer | type[Placer] | tuple[type[Placer], dict] | None = None,
        router: Router | type[Router] | tuple[type[Router], dict] | None = None,
        iterations: int = 10,
        coupling_map: tuple[int, int] | None = None,
    ) -> tuple[list[gates.Gate], int, list[int]]:
        """Routes the virtual/logical qubits of a circuit to the physical qubits of a chip. Returns and logs the final qubit layout.

        This process uses the provided ``placer``, ``router``, and ``routing_iterations`` parameters if they are passed; otherwise, default values are applied.

        **Examples:**

        If we instantiate some ``Circuit``, ``Platform`` and ``CircuitTranspiler`` objects like:

        .. code-block:: python

            from qibo import gates
            from qibo.models import Circuit
            from qibo.transpiler.placer import ReverseTraversal, Random
            from qibo.transpiler.router import Sabre
            from qililab import build_platform
            from qililab.digital import CircuitTranspiler

            # Create circuit:
            c = Circuit(5)
            c.add(gates.CNOT(1, 0))

            # Create platform:
            platform = build_platform(runcard="<path_to_runcard>")
            coupling_map = platform.digital_compilation_settings.topology

            # Create transpiler:
            transpiler = CircuitTranspiler(platform.digital_compilation_settings)

        Now we can transpile like:

        .. code-block:: python

            # Default Transpilation:
            routed_circuit, qubits, final_layouts = transpiler.route_circuit(c)  # Defaults to ReverseTraversal, Sabre and platform connectivity

            # Non-Default Random placer, and coupling_map specified:
            routed_circuit, qubits, final_layouts = transpiler.route_circuit(c, placer=Random, router=Sabre, coupling_map)

            # Specifying one of the a kwargs:
            routed_circuit, qubits, final_layouts = transpiler.route_circuit(c, placer=Random, router=(Sabre, {"lookahead": 2}))

        Args:
            circuit (Circuit): circuit to route.
            placer (Placer | type[Placer] | tuple[type[Placer], dict], optional): ``Placer`` instance, or subclass ``type[Placer]`` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to ``ReverseTraversal``.
            router (Router | type[Router] | tuple[type[Router], dict], optional): ``Router`` instance, or subclass ``type[Router]`` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to ``Sabre``.
            iterations (int, optional): Number of times to repeat the routing pipeline, to keep the best stochastic result. Defaults to 10.
            coupling_map (tuple[int, int], optional): coupling map of the chip to route. This topology will be the one that rules,
                which will overwrite any other in an instance of router or placer. Defaults to the platform topology.

        Returns:
            tuple[list[Gate], int, list[int]]: List of gates of the routed circuit, number of qubits in it, and its corresponding final layout (Initial
                Re-mapping + SWAPs routing) of the Original Logical Qubits (l_q) in the physical circuit (wires): [l_q in wire 0, l_q in wire 1, ...].

        Raises:
            ValueError: If StarConnectivity Placer and Router are used with non-star topologies.
        """
        # Get the chip's connectivity
        topology = nx.Graph(coupling_map if coupling_map is not None else self.settings.topology)
        circuit_router = CircuitRouter(topology, placer, router)

        circuit, final_layout = circuit_router.route(circuit, iterations)

        return circuit.queue, circuit.nqubits, final_layout

    @staticmethod
    def optimize_gates(circuit_gates: list[gates.Gate]) -> list[gates.Gate]:
        """Main method to optimize the gates of a Quantum Circuit before unrolling to native gates.

        Currently only applies a cancellation for adjacent hermitian gates (H, X, Y, Z, CNOT, CZ, SWAP).

        The total optimization can/might be expanded in the future to include more complex gate optimization.

        Args:
            circuit_gates (list[gates.Gate]): list of gates of the Qibo circuit to optimize.

        Returns:
            list[gates.Gate]: list of the gates of the Qibo circuit, optimized.
        """
        return CircuitOptimizer.optimize_gates(circuit_gates)

    @staticmethod
    def gates_to_native(circuit_gates: list[gates.Gate]) -> list[gates.Gate]:
        """Maps Qibo gates to a hardware native implementation (CZ, RZ, Drag, Wait and M (Measurement))
            - CZ gates are our 2 qubit gates
            - RZ gates are applied as virtual Z gates if optimize=True in the transpiler
            - Drag gates are our single qubit gates
            - Wait gates add wait time at a single qubit
            - Measurement gates measure the circuit

        Args:
            circuit_gates (list[gates.Gate]): list of gates of the Qibo circuit, to pass to native.

        Returns:
            list[gates.Gate]: list of native gates of the Qibo circuit.

        """
        return translate_gates(circuit_gates)

    def add_phases_from_RZs_and_CZs_to_drags(self, circuit_gates: list[gates.Gate], nqubits: int) -> list[gates.Gate]:
        """This method adds the phases from RZs and CZs gates of the circuit to the next Drag gates.

            - The CZs added phases on the Drags, come from a correction from their calibration, stored on the setting of the CZs.
            - The RZs added phases on the Drags, come from commuting all the RZs all the way to the end of the circuit, so they can be deleted as "virtual Z gates".

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
            circuit_gates (list[gates.Gate]): list of native gates of the circuit, to pass phases to the Drag gates.
            nqubits (int): Number of qubits of the circuit.

        Returns:
            list[gates.Gate]: list of native gates of the circuit, with phases passed to the Drag gates.
        """
        return self.optimizer.add_phases_from_RZs_and_CZs_to_drags(circuit_gates, nqubits)

    def optimize_transpiled_gates(self, circuit_gates: list[gates.Gate]) -> list[gates.Gate]:
        """Main method to optimize the gates of a Quantum Circuit after having unrolled to native gates.

        Currently only bunches consecutive Drag gates, with same phi's, together into a single one, and removes redundant Drag gates.

        The total optimization can/might be expanded in the future to include more complex optimizations.

        Args:
            circuit_gates (list[gates.Gate]): list of gates of the transpiled circuit, to optimize.

        Returns:
            list[gates.Gate]: list of gates of the transpiled circuit, optimized.
        """
        return self.optimizer.optimize_transpiled_gates(circuit_gates)

    def gates_to_pulses(self, circuit_gates: list[gates.Gate]) -> PulseSchedule:
        """Translates a Qibo circuit into its corresponding pulse sequences.

        For each circuit gate we look up for its corresponding gates settings in the runcard (the name of the class of the circuit
        gate and the name of the gate in the runcard should match) and load its schedule of GateEvents.

        Each gate event corresponds to a concrete pulse applied at a certain time w.r.t the gate's start time and through a specific bus
        (see gates settings docstrings for more details).

        Measurement gates are handled in a slightly different manner. For a circuit gate M(0,1,2) the settings for each M(0), M(1), M(2)
        will be looked up and will be applied in sync. Note that thus a circuit gate for M(0,1,2) is different from the circuit sequence
        M(0)M(1)M(2) since the later will not be necessarily applied at the same time for all the qubits involved.

        Times for each qubit are kept track of with the dictionary ``time``.

        The times at which each pulse is applied are padded if they are not multiples of the minimum clock time. This means that if min clock
        time is 4 and a pulse applied to qubit k lasts 17ns, the next pulse at qubit k will be at t=20ns

        Args:
            circuit_gates (list[gates.Gate]): list of native gates of the Qibo circuit.

        Returns:
            PulseSequences: equivalent :class:`PulseSequences` class.
        """
        circuit_to_pulses = CircuitToPulses(self.settings)

        return circuit_to_pulses.run(circuit_gates)

    @staticmethod
    def _check_that_no_SWAP_gate_is_after_measurement(circuit: Circuit, before_or_after: str) -> None:
        """Checks that no SWAP gate is after a measurement gate in each qubit of the circuit.

        Args:
            circuit (Circuit): Qibo circuit to check.
            before_or_after (str): Whether to check before or after the measurement gate. Should be "before" or "after".

        Raises:
            ValueError: If there is a gate after a measurement gate.
        """
        for qubit in range(circuit.nqubits):
            first_measurement = None
            last_SWAP = None
            for i, gate in enumerate(circuit.queue):
                if qubit in gate.qubits:
                    if isinstance(gate, M):
                        first_measurement = i if first_measurement is None else first_measurement
                    elif isinstance(gate, SWAP):
                        last_SWAP = i
            if first_measurement is not None and last_SWAP is not None and first_measurement < last_SWAP:
                # Error if SWAP is after Measurement in original circuit
                if before_or_after == "before":
                    raise ValueError(
                        f"Automatic routing requires that no SWAP gate appears after a Measurement gate on any qubit.Review the circuit gates for qubit {qubit}."
                    )
                # Error if SWAP gate has been added after Measurement in routing
                if before_or_after == "after":
                    raise ValueError(
                        f"Routing error: A SWAP gate was added after a Measurement on qubit {qubit}, which is not allowed in automatic routing. This likely occurred because 2-qubit gates were used after a Measurement. To route such circuits, use `CircuitRouter` manually and track the mapping of measurement results before execution."
                    )
