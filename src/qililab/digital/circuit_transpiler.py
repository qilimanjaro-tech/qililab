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

from dataclasses import asdict

import networkx as nx
import numpy as np
from qibo import gates
from qibo.gates import Gate, M
from qibo.models import Circuit
from qibo.transpiler.placer import Placer
from qibo.transpiler.router import Router

from qililab.config import logger
from qililab.constants import RUNCARD
from qililab.digital.circuit_router import CircuitRouter
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings
from qililab.settings.digital.gate_event_settings import GateEventSettings
from qililab.typings.enums import Line
from qililab.utils import Factory

from .gate_decompositions import translate_gates
from .native_gates import Drag, Wait


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
    ) -> tuple[list[PulseSchedule], list[dict]]:
        """Transpiles a list of ``qibo.models.Circuit`` to a list of pulse schedules.

        First makes a routing and placement of the circuit to the chip's physical qubits. And returns/logs the final layout of the qubits.

        Then translates the circuit to a native gate circuit and applies virtual Z gates and phase corrections for CZ gates.

        And finally, it converts the native gate circuit to a pulse schedule using calibrated settings from the runcard.

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

        Now we can transpile like:

        .. code-block:: python

            # Default Transpile:
            pulse_schedule, final_layouts = transpiler.transpile_circuit([c])  # Defaults to ReverseTraversal, Sabre

            # Non-Default Trivial placer, and Default Router, but with its kwargs specified:
            pulse_sched, final_layouts = transpiler.transpile_circuit([c], placer=Trivial, router=(Sabre, {"lookahead": 2}))


        Args:
            circuits (list[Circuit]): list of qibo circuits.
            placer (Placer | type[Placer] | tuple[type[Placer], dict], optional): `Placer` instance, or subclass `type[Placer]` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `ReverseTraversal`.
            router (Router | type[Router] | tuple[type[Router], dict], optional): `Router` instance, or subclass `type[Router]` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `Sabre`.
            routing_iterations (int, optional): Number of times to repeat the routing pipeline, to get the best stochastic result. Defaults to 10.

        Returns:
            list[PulseSchedule]: list of pulse schedules.
            list[dict]: list of the final layouts of the qubits, in each circuit.
        """
        routed_circuits, final_layouts = zip(
            *(self.route_circuit(circuit, placer, router, iterations=routing_iterations) for circuit in circuits)
        )
        logger.info(f"Circuits final layouts: {final_layouts}")

        native_circuits = (self.circuit_to_native(circuit) for circuit in routed_circuits)
        return self.circuit_to_pulses(list(native_circuits)), list(final_layouts)

    def route_circuit(
        self,
        circuit: Circuit,
        placer: Placer | type[Placer] | tuple[type[Placer], dict] | None = None,
        router: Router | type[Router] | tuple[type[Router], dict] | None = None,
        coupling_map: list[tuple[int, int]] | None = None,
        iterations: int = 10,
    ) -> tuple[Circuit, dict]:
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
            coupling_map (list[tuple[int, int]], optional): coupling map of the chip. Defaults to the platform topology.
            placer (Placer | type[Placer] | tuple[type[Placer], dict], optional): `Placer` instance, or subclass `type[Placer]` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `ReverseTraversal`.
            router (Router | type[Router] | tuple[type[Router], dict], optional): `Router` instance, or subclass `type[Router]` to
                use, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `Sabre`.
            iterations (int, optional): Number of times to repeat the routing pipeline, to keep the best stochastic result. Defaults to 10.


        Returns:
            Circuit: routed circuit.
            dict: final layout of the circuit.

        Raises:
            ValueError: If StarConnectivity Placer and Router are used with non-star topologies.
        """
        # Get the chip's connectivity
        topology = nx.Graph(coupling_map if coupling_map is not None else self.digital_compilation_settings.topology)

        circuit_router = CircuitRouter(topology, placer, router)

        return circuit_router.route(circuit, iterations)

    def circuit_to_native(self, circuit: Circuit, optimize: bool = True) -> Circuit:
        """Converts circuit with qibo gates to circuit with native gates

        Args:
            circuit (Circuit): circuit with qibo gates
            optimize (bool): optimize the transpiled circuit using otpimize_transpilation

        Returns:
            new_circuit (Circuit): circuit with transpiled gates
        """
        # init new circuit
        new_circuit = Circuit(circuit.nqubits)
        # add transpiled gates to new circuit, optimize if needed
        if optimize:
            gates_to_optimize = translate_gates(circuit.queue)
            new_circuit.add(self.optimize_transpilation(circuit.nqubits, ngates=gates_to_optimize))
        else:
            new_circuit.add(translate_gates(circuit.queue))

        return new_circuit

    def optimize_transpilation(self, nqubits: int, ngates: list[gates.Gate]) -> list[gates.Gate]:
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
            nqubits (int) : number of qubits in the circuit
            ngates (list[gates.Gate]) : list of gates in the circuit

        Returns:
            list[gates.Gate] : list of re-ordered gates
        """
        supported_gates = ["rz", "drag", "cz", "wait", "measure"]
        new_gates = []
        shift = dict.fromkeys(range(nqubits), 0)
        for gate in ngates:
            if gate.name not in supported_gates:
                raise NotImplementedError(f"{gate.name} not part of native supported gates {supported_gates}")
            if isinstance(gate, gates.RZ):
                shift[gate.qubits[0]] += gate.parameters[0]
            # add CZ phase correction
            elif isinstance(gate, gates.CZ):
                gate_settings = self.digital_compilation_settings.get_gate(
                    name=gate.__class__.__name__, qubits=gate.qubits
                )
                control_qubit, target_qubit = gate.qubits
                corrections = next(
                    (
                        event.pulse.options
                        for event in gate_settings
                        if (
                            event.pulse.options is not None
                            and f"q{control_qubit}_phase_correction" in event.pulse.options
                        )
                    ),
                    None,
                )
                if corrections is not None:
                    shift[control_qubit] += corrections[f"q{control_qubit}_phase_correction"]
                    shift[target_qubit] += corrections[f"q{target_qubit}_phase_correction"]
                new_gates.append(gate)
            else:
                # if gate is drag pulse, shift parameters by accumulated Zs
                if isinstance(gate, Drag):
                    # create new drag pulse rather than modify parameters of the old one
                    gate = Drag(gate.qubits[0], gate.parameters[0], gate.parameters[1] - shift[gate.qubits[0]])

                # append gate to optimized list
                new_gates.append(gate)

        return new_gates

    def circuit_to_pulses(self, circuits: list[Circuit]) -> list[PulseSchedule]:
        """Translates a list of circuits into a list of pulse sequences (each circuit to an independent pulse sequence)
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

        pulse_schedule_list: list[PulseSchedule] = []
        for circuit in circuits:
            pulse_schedule = PulseSchedule()
            time: dict[int, int] = {}  # init/restart time
            for gate in circuit.queue:
                # handle wait gates
                if isinstance(gate, Wait):
                    self._update_time(time=time, qubit=gate.qubits[0], gate_time=gate.parameters[0])
                    continue

                # Measurement gates need to be handled on their own because qibo allows to define
                # an M gate as eg. gates.M(*range(5))
                if isinstance(gate, M):
                    gate_schedule = []
                    gate_qubits = gate.qubits
                    for qubit in gate_qubits:
                        gate_schedule += self._gate_schedule_from_settings(M(qubit))

                # handle control gates
                else:
                    # extract gate schedule
                    gate_schedule = self._gate_schedule_from_settings(gate)
                    gate_qubits = self._get_gate_qubits(gate, gate_schedule)

                # process gate_schedule to pulses for both M and control gates
                # get total duration for the gate
                gate_time = self._get_total_schedule_duration(gate_schedule)
                # update time, start time is that of the qubit most ahead in time
                start_time = 0
                for qubit in gate_qubits:
                    start_time = max(self._update_time(time=time, qubit=qubit, gate_time=gate_time), start_time)
                # sync gate end time
                self._sync_qubit_times(gate_qubits, time=time)
                # apply gate schedule
                for gate_event in gate_schedule:
                    # add control gate schedule
                    pulse_event = self._gate_element_to_pulse_event(time=start_time, gate=gate, gate_event=gate_event)
                    # pop first qubit from gate if it is measurement
                    # this is so that the target qubit for multiM gates is every qubit in the M gate
                    if isinstance(gate, M):
                        gate = M(*gate.qubits[1:])
                    # add event
                    delay = self.digital_compilation_settings.buses[gate_event.bus].delay
                    pulse_schedule.add_event(pulse_event=pulse_event, bus_alias=gate_event.bus, delay=delay)  # type: ignore

            for bus_alias in self.digital_compilation_settings.buses:
                # If we find a flux port, create empty schedule for that port.
                # This is needed because for Qblox instrument working in flux buses as DC sources, if we don't
                # add an empty schedule its offsets won't be activated and the results will be misleading.
                if self.digital_compilation_settings.buses[bus_alias].line == Line.FLUX:
                    pulse_schedule.create_schedule(bus_alias=bus_alias)

            pulse_schedule_list.append(pulse_schedule)

        return pulse_schedule_list

    def _gate_schedule_from_settings(self, gate: Gate) -> list[GateEventSettings]:
        """Gets the gate schedule. The gate schedule is the list of pulses to apply
        to a given bus for a given gate

        Args:
            gate (Gate): Qibo gate

        Returns:
            list[GateEventSettings]: schedule list with each of the pulses settings
        """

        gate_schedule = self.digital_compilation_settings.get_gate(name=gate.__class__.__name__, qubits=gate.qubits)

        if not isinstance(gate, Drag):
            return gate_schedule

        # drag gates are currently the only parametric gates we are handling and they are handled here
        if len(gate_schedule) > 1:
            raise ValueError(
                f"Schedule for the drag gate is expected to have only 1 pulse but instead found {len(gate_schedule)} pulses"
            )
        drag_schedule = GateEventSettings(
            **asdict(gate_schedule[0])
        )  # make new object so that gate_schedule is not overwritten
        theta = self._normalize_angle(angle=gate.parameters[0])
        amplitude = drag_schedule.pulse.amplitude * theta / np.pi
        phase = self._normalize_angle(angle=gate.parameters[1])
        if amplitude < 0:
            amplitude = -amplitude
            phase = self._normalize_angle(angle=gate.parameters[1] + np.pi)
        drag_schedule.pulse.amplitude = amplitude
        drag_schedule.pulse.phase = phase
        return [drag_schedule]

    def _normalize_angle(self, angle: float):
        """Normalizes angle in range [-pi, pi].

        Args:
            angle (float): Normalized angle.
        """
        angle %= 2 * np.pi
        if angle > np.pi:
            angle -= 2 * np.pi
        return angle

    def _get_total_schedule_duration(self, schedule: list[GateEventSettings]) -> int:
        """Returns total time for a gate schedule. This is done by taking the max of (init + duration)
        for all the elements in the schedule

        Args:
            schedule (list[CircuitPulseSettings]): Schedule of pulses to apply

        Returns:
            int: Total gate time
        """
        time = 0
        for schedule_element in schedule:
            time = max(time, schedule_element.pulse.duration + schedule_element.wait_time)
        return time

    def _get_gate_qubits(self, gate: Gate, schedule: list[GateEventSettings] | None = None) -> tuple[int, ...]:
        """Gets qubits involved in gate. This includes gate.qubits but also qubits which are targets of
        buses in the gate schedule

        Args:
            schedule (list[CircuitPulseSettings]): Gate schedule

        Returns:
            list[int]: list of qubits
        """

        schedule_qubits = (
            [
                qubit
                for schedule_element in schedule
                for qubit in self.digital_compilation_settings.buses[schedule_element.bus].qubits
                if schedule_element.bus in self.digital_compilation_settings.buses
            ]
            if schedule is not None
            else []
        )

        gate_qubits = list(gate.qubits)

        return tuple(set(schedule_qubits + gate_qubits))  # convert to set and back to list to remove repeated items

    def _gate_element_to_pulse_event(self, time: int, gate: Gate, gate_event: GateEventSettings) -> PulseEvent:
        """Translates a gate element into a pulse.

        Args:
            time (dict[int, int]): dictionary containing qubit indices as keys and current time (ns) as values
            gate (gate): circuit gate. This is used only to know the qubit target of measurement gates
            gate_event (GateEventSettings): gate event, a single element of a gate schedule containing information
            about the pulse to be applied
            bus (bus): bus through which the pulse is sent

        Returns:
            PulseEvent: pulse event corresponding to the input gate event
        """

        # copy to avoid modifying runcard settings
        pulse = gate_event.pulse
        pulse_shape_copy = pulse.shape.copy()
        pulse_shape = Factory.get(pulse_shape_copy.pop(RUNCARD.NAME))(**pulse_shape_copy)

        # handle measurement gates and target qubits for control gates which might have multi-qubit schedules
        bus = self.digital_compilation_settings.buses[gate_event.bus]
        qubit = (
            gate.qubits[0]
            if isinstance(gate, M)
            else next((qubit for qubit in bus.qubits), None)
            if bus is not None
            else None
        )

        return PulseEvent(
            pulse=Pulse(
                amplitude=pulse.amplitude,
                phase=pulse.phase,
                duration=pulse.duration,
                frequency=0,
                pulse_shape=pulse_shape,
            ),
            start_time=time + gate_event.wait_time + self.digital_compilation_settings.delay_before_readout,
            pulse_distortions=bus.distortions,
            qubit=qubit,
        )

    def _update_time(self, time: dict[int, int], qubit: int, gate_time: int):
        """Creates new timeline if not already created and update time.

        Args:
            time (Dict[int, int]): Dictionary with the time of each qubit.
            qubit_idx (int): qubit index
            gate_time (int): total duration of the gate
        """
        if qubit not in time:
            time[qubit] = 0
        old_time = time[qubit]
        residue = (gate_time) % self.digital_compilation_settings.minimum_clock_time
        if residue != 0:
            gate_time += self.digital_compilation_settings.minimum_clock_time - residue
        time[qubit] += gate_time
        return old_time

    def _sync_qubit_times(self, qubits: list[int], time: dict[int, int]):
        """Syncs the time of the given qubit list

        Args:
            qubits (list[int]): qubits to sync
            time (dict[int,int]): time dictionary
        """
        max_time = max((time[qubit] for qubit in qubits if qubit in time), default=0)
        for qubit in qubits:
            time[qubit] = max_time
