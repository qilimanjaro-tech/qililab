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

from typing import TYPE_CHECKING

import networkx as nx

from qililab.config import logger
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


class CircuitTranspiler:
    """Handles circuit transpilation. It has 3 accessible methods:

    - ``circuit_to_native``: transpiles a qibo circuit to native gates (Drag, CZ, Wait, M) and optionally RZ if optimize=False (optimize=True by default)
    - ``circuit_to_pulses``: transpiles a native gate circuit to a `PulseSchedule`
    - ``transpile_circuit``: runs both of the methods above sequentially

    Args:
        settings (DigitalCompilationSettings): Object containing the Digital Compilations Settings and the info on chip's physical qubits.
            It can be obtained from the `digital_compilation_settings` attribute of a `Platform` object.
    """

    def __init__(self, settings: DigitalCompilationSettings):
        self.settings: DigitalCompilationSettings = settings
        """Object containing the digital compilations settings and the info on chip's physical qubits."""

        self.optimizer: CircuitOptimizer = CircuitOptimizer(self.settings)
        """Object to do do the complex circuit manipulations with."""

    def transpile_circuit(
        self,
        circuit: Circuit,
        routing: bool = False,
        placer: Placer | type[Placer] | tuple[type[Placer], dict] | None = None,
        router: Router | type[Router] | tuple[type[Router], dict] | None = None,
        routing_iterations: int = 10,
        optimize: bool = False,
    ) -> tuple[PulseSchedule, dict[str, int]]:
        """Transpiles a list of ``qibo.models.Circuit`` objects into a list of pulse schedules.

        The process involves the following steps:

        1. \\*)Routing and Placement: Routes and places the circuit's logical qubits onto the chip's physical qubits. The final qubit layout is returned and logged. This step uses the ``placer``, ``router``, and ``routing_iterations`` parameters from ``transpile_config`` if provided; otherwise, default values are applied. Refer to the :meth:`.CircuitTranspiler.route_circuit()` method for more information.

        2. \\**)Canceling adjacent pairs of Hermitian gates (H, X, Y, Z, CNOT, CZ, and SWAPs). Refer to the :meth:`.CircuitTranspiler.optimize_gates()` method for more information.

        3. Native Gate Translation: Translates the circuit into the chip's native gate set (CZ, RZ, Drag, Wait, and M (Measurement)). Refer to the :meth:`.CircuitTranspiler.gates_to_native()` method for more information.

        4. Adding phases to our Drag gates, due to commuting RZ gates until the end of the circuit to discard them as virtual Z gates, and due to the phase corrections from CZ. Refer to the :meth:`.CircuitTranspiler.add_phases_from_RZs_and_CZs_to_drags()` method for more information.

        5. \\**)Optimizing the resulting Drag gates, by combining multiple pulses into a single one. Refer to the :meth:`.CircuitTranspiler.optimize_transpiled_gates()` method for more information.

        6. Pulse Schedule Conversion: Converts the native gates into a pulse schedule using calibrated settings from the runcard. Refer to the :meth:`.CircuitTranspiler.gates_to_pulses()` method for more information.

        .. note::

            \\*) If ``routing=False`` (default behavior), step 1. is skipped.

            \\**) If ``optimize=False`` (default behavior), steps 2. and 5. are skipped.

            The rest of steps are always done.

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
            transpiler = CircuitTranspiler(platform.digital_compilation_settings)

        Now we can transpile like, in the following examples:

        .. code-block:: python

            # Default Transpilation (with ReverseTraversal, Sabre, platform's connectivity and optimize = True):
            transpiled_circuit, final_layouts = transpiler.transpile_circuit(c)

            # Or another case, not doing optimization for some reason, and with Non-Default placer:
            transpiled_circuit, final_layout = transpiler.transpile_circuit(c, placer=Trivial, optimize=False)

            # Or also specifying the `router` with kwargs:
            transpiled_circuit, final_layouts = transpiler.transpile_circuit(c, router=(Sabre, {"lookahead": 2}))

        .. note::

            Check :ref:`Transpilation <transpilation>`, for more examples of how ``execute()``'s methods automatically apply this.

        Args:
            circuit (Circuit): Qibo circuit.
            routing (bool, optional): whether to route the circuit. Defaults to False.
            placer (Placer | type[Placer] | tuple[type[Placer], dict], optional): ``Placer`` instance, or subclass ``type[Placer]`` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to ``ReverseTraversal``.
            router (Router | type[Router] | tuple[type[Router], dict], optional): ``Router`` instance, or subclass ``type[Router]`` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to ``Sabre``.
            routing_iterations (int, optional): Number of times to repeat the routing pipeline, to get the best stochastic result. Defaults to 10.
            optimize (bool, optional): whether to optimize the circuit and/or transpilation. Defaults to True.

        Returns:
            tuple[PulseSchedule, dict[str, int]]: Pulse schedule and final layouts of the qubits, in the circuit {"qI": J}.
        """

        # Routing stage;
        if routing:
            gate_list, final_layout, nqubits = self.route_circuit(circuit, placer, router, routing_iterations)
        else:
            gate_list, nqubits = circuit.queue, circuit.nqubits
            final_layout = {f"q{i}": i for i in range(nqubits)}

        # Optimze qibo gates, cancelling redundant gates:
        if optimize:
            gate_list = self.optimize_gates(gate_list)

        # Unroll to Natives gates:
        gate_list = self.gates_to_native(gate_list)

        # Add phases from RZs and CZs to Drags:
        gate_list = self.add_phases_from_RZs_and_CZs_to_drags(gate_list, nqubits)

        # Optimze transpiled qibo gates, cancelling redundant gates:
        if optimize:
            gate_list = self.optimize_transpiled_gates(gate_list)

        # Pulse schedule stage:
        pulse_schedule = self.gates_to_pulses(gate_list)

        return pulse_schedule, final_layout

    def route_circuit(
        self,
        circuit: Circuit,
        placer: Placer | type[Placer] | tuple[type[Placer], dict] | None = None,
        router: Router | type[Router] | tuple[type[Router], dict] | None = None,
        iterations: int = 10,
        coupling_map: list[tuple[int, int]] | None = None,
    ) -> tuple[list[gates.Gate], dict[str, int], int]:
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
            placer (Placer | type[Placer] | tuple[type[Placer], dict], optional): `Placer` instance, or subclass `type[Placer]` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `ReverseTraversal`.
            router (Router | type[Router] | tuple[type[Router], dict], optional): `Router` instance, or subclass `type[Router]` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `Sabre`.
            iterations (int, optional): Number of times to repeat the routing pipeline, to keep the best stochastic result. Defaults to 10.
            coupling_map (list[tuple[int, int]], optional): coupling map of the chip to route. This topology will be the one that rules,
                which will overwrite any other in an instance of router or placer. Defaults to the platform topology.

        Returns:
            tuple[list[Gate], dict[str, int], int]: List of gates of the routed circuit, final layout of the circuit {"qI": J}, and number of qubits in the final circuit.

        Raises:
            ValueError: If StarConnectivity Placer and Router are used with non-star topologies.
        """
        # Get the chip's connectivity
        topology = nx.Graph(coupling_map if coupling_map is not None else self.settings.topology)
        circuit_router = CircuitRouter(topology, placer, router)

        circuit, final_layout = circuit_router.route(circuit, iterations)
        logger.info(f"The physical qubits used for the execution will be: {final_layout}")

        return circuit.queue, final_layout, circuit.nqubits

    @staticmethod
    def optimize_gates(gate_list: list[gates.Gate]) -> list[gates.Gate]:
        """Main function to optimize the circuit with. Currently works by cancelling adjacent hermitian gates.

        The total optimization can/might be expanded in the future.

        Args:
            gate_list (list[gates.Gate]): list of gates of the Qibo circuit to optimize.

        Returns:
            list[gates.Gate]: list of the gates of the Qibo circuit, optimized.
        """
        return CircuitOptimizer.optimize_gates(gate_list)

    @staticmethod
    def gates_to_native(gate_list: list[gates.Gate]) -> list[gates.Gate]:
        """Maps Qibo gates to a hardware native implementation (CZ, RZ, Drag, Wait and M (Measurement))
            - CZ gates are our 2 qubit gates
            - RZ gates are applied as virtual Z gates if optimize=True in the transpiler
            - Drag gates are our single qubit gates
            - Wait gates add wait time at a single qubit
            - Measurement gates measure the circuit

        Args:
            gate_list (list[gates.Gate]): list of gates of the Qibo circuit, to pass to native.

        Returns:
            list[gates.Gate]: list of native gates of the Qibo circuit.

        """
        return translate_gates(gate_list)

    def add_phases_from_RZs_and_CZs_to_drags(self, gate_list: list[gates.Gate], nqubits: int) -> list[gates.Gate]:
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
            gate_list (list[gates.Gate]): list of native gates of the circuit, to pass phases to the Drag gates.
            nqubits (int): Number of qubits of the circuit.

        Returns:
            list[gates.Gate]: list of native gates of the circuit, with phases passed to the Drag gates.
        """
        return self.optimizer.add_phases_from_RZs_and_CZs_to_drags(gate_list, nqubits)

    def optimize_transpiled_gates(self, gate_list: list[gates.Gate]) -> list[gates.Gate]:
        """Bunches consecutive Drag gates together into a single one.

        Args:
            gate_list (list[gates.Gate]): list of gates of the transpiled circuit, to optimize.

        Returns:
            list[gates.Gate]: list of gates of the transpiled circuit, optimized.
        """
        return self.optimizer.optimize_transpiled_gates(gate_list)

    def gates_to_pulses(self, gate_list: list[gates.Gate]) -> PulseSchedule:
        """Translates a Qibo circuit into its corresponding pulse sequences.

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
            gate_list (list[gates.Gate]): list of native gates of the Qibo circuit.

        Returns:
            PulseSequences: equivalent :class:`PulseSequences` class.
        """
        circuit_to_pulses = CircuitToPulses(self.settings)

        return circuit_to_pulses.run(gate_list)
