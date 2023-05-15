"""Class that translates a Qibo Circuit into a PulseSequence"""
import ast
from dataclasses import asdict, dataclass

import numpy as np
from qibo.gates import CZ, Gate, M
from qibo.models.circuit import Circuit

from qililab.chip import Chip
from qililab.chip.nodes import Port, Qubit
from qililab.constants import RUNCARD
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.settings import RuncardSchema
from qililab.transpiler import Drag
from qililab.utils import Factory

# TODO IMPORTANT set flux pulse line for cz gate
# parking


@dataclass
class CircuitToPulses:
    """Class that translates a Qibo Circuit into a PulseSequence"""

    settings: RuncardSchema.PlatformSettings

    def __post_init__(self):
        """Post init."""
        self._instantiate_gates_from_settings()

    def translate(self, circuits: list[Circuit], chip: Chip) -> list[PulseSchedule]:
        """Translate each circuit to a PulseSequences class, which is a list of PulseSequence classes for
        each different port and pulse name (control/readout).

        Args:
            circuits (List[Circuit]): List of Qibo Circuit classes.
            chip (Chip): Chip representation as a graph.

        Returns:
            list[PulseSequences]: List of PulseSequences classes.
        """
        pulse_schedule_list: list[PulseSchedule] = []
        for circuit in circuits:
            pulse_schedule = PulseSchedule()
            time: dict[int, int] = {}  # restart time

            # separate measurement gates from control gates
            readout_gates = []
            control_gates = []
            for i, gate in enumerate(circuit.queue):
                if isinstance(gate, M):
                    readout_gates.append((i, gate))
                else:
                    control_gates.append(gate)

            for gate in control_gates:
                pulse_event, port = self._control_gate_to_pulse_event(time=time, control_gate=gate, chip=chip)
                if pulse_event is not None:
                    pulse_schedule.add_event(pulse_event=pulse_event, port=port)
            for _, readout_gate in readout_gates:
                for qubit_idx in readout_gate.target_qubits:
                    readout_pulse_event, port = self._readout_gate_to_pulse_event(
                        time=time, readout_gate=readout_gate, qubit_idx=qubit_idx, chip=chip
                    )
                    if readout_pulse_event is not None:
                        pulse_schedule.add_event(pulse_event=readout_pulse_event, port=port)

            pulse_schedule_list.append(pulse_schedule)

        return pulse_schedule_list

    def _build_pulse_shape_from_gate_settings(self, gate_settings: HardwareGate.HardwareGateSettings):
        """Build Pulse Shape from Gate settings

        Args:
            gate_settings (HardwareGateSettings): gate settings loaded from the runcard

        Returns:
            shape_settings (dict): shape settings for the gate's pulse
        """
        shape_settings = gate_settings.shape.copy()
        return Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)

    def _control_gate_to_pulse_event(
        self, time: dict[int, int], control_gate: Gate, chip: Chip
    ) -> tuple[PulseEvent | None, int]:
        """Translate a gate into a pulse event.

        Args:
            time (dict[int, int]): dictionary containing qubit indices as keys and current time (ns) as values
            control_gate (Gate): non-measurement gate from circuit
            chip (Chip): chip representation as a graph.

        Returns:
            PulseEvent: PulseEvent object.

        For a Drag pulse R(a,b) the corresponding pulse will have amplitude a/pi * qubit_pi_amp
        where qubit_pi_amp is the amplitude of the pi pulse for the given qubit calibrated from Rabi.
        The phase will correspond to the rotation around Z from b in R(a,b)
        """
        gate_settings = self._get_gate_settings_with_master_values(gate=control_gate)
        pulse_shape = self._build_pulse_shape_from_gate_settings(gate_settings=gate_settings)
        # for CZs check if they are possible and switch target if needed
        if isinstance(control_gate, CZ):
            control_gate = self._parse_check_cz(control_gate)

        qubit_idx = control_gate.target_qubits[0]
        node = chip.get_node_from_qubit_idx(idx=qubit_idx, readout=False)

        # TODO: CZ port here
        # TODO: SNZ duration is 2 * gate.duration + t_phi + 2
        # TODO: park pulse here

        # TODO implement this inside chip class
        # get ports and select those we need
        adj_nodes = chip._get_adjacent_nodes(node)
        # get adjacent node if it is a drive line
        if not isinstance(control_gate, CZ):
            for adj_node in adj_nodes:
                if isinstance(adj_node, Port) and adj_node.name[: len("drive_line")] == "drive_line":
                    port = adj_node.id_
        # for CZ gates we need flux drive and adjacent qubits if parking
        else:
            parking = "parking" in [gate.name for gate in self.settings.gates[control_gate.qubits]]
            parking_qubits = []
            for adj_node in adj_nodes:
                # get flux line
                if isinstance(adj_node, Port) and adj_node.name[: len("flux_line")] == "flux_line":
                    port = adj_node.id_
                # get adj qubits
                elif parking and isinstance(adj_node, Qubit):
                    parking_qubits.append(adj_node.qubit_index)
        if not isinstance(port, Port):
            raise RuntimeError(
                f"Wrong or no port found for gate {control_gate} and qubit {qubit_idx} with node id {node.id_}"
            )
        if parking and len(parking_qubits) < 1:
            raise RuntimeError(
                f"{len(parking_qubits)} adjacent qubits found for qubit {qubit_idx} with node id {node.id_}. There should be more than 1 adjacent qubit for a CZ gate with parking"
            )

        old_time = self._update_time(
            time=time,
            qubit_idx=qubit_idx,
            pulse_time=gate_settings.duration + self.settings.delay_between_pulses,
        )

        # load amplitude, phase for drag pulse from circuit gate parameters
        if isinstance(control_gate, Drag):
            amplitude = (control_gate.parameters[0] / np.pi) * gate_settings.amplitude
            phase = control_gate.parameters[1]
            # phase is given by b in Drag(a,b) so there should not be any phase defined at gate settings (runcard)
            if gate_settings.phase is not None:
                raise ValueError(
                    "Drag gate should not have setting for phase since the phase depends only on circuit gate parameters"
                )
        else:
            amplitude = float(gate_settings.amplitude)
            phase = float(gate_settings.phase)

        return (
            PulseEvent(
                pulse=Pulse(
                    amplitude=amplitude,
                    phase=phase,
                    duration=gate_settings.duration,
                    pulse_shape=pulse_shape,
                    frequency=node.frequency,
                ),
                start_time=old_time,
            )
            if gate_settings.duration > 0
            else None,
            port,
        )

    def _readout_gate_to_pulse_event(
        self, time: dict[int, int], readout_gate: Gate, qubit_idx: int, chip: Chip
    ) -> tuple[PulseEvent | None, int]:
        """Translate a gate into a pulse.

        Args:
            time (dict[int, int]): dictionary containing qubit indices as keys and current time (ns) as values
            readout_gate (Gate): measurement gate
            qubit_id (int): qubit number (note that the first qubit is the 0th).
            chip (Chip): chip representation as a graph.

        Returns:
            tuple[PulseEvent | None, int]: (PulseEvent or None, port_id).
        """
        gate_settings = self._get_gate_settings_with_master_values(gate=readout_gate)
        shape_settings = gate_settings.shape.copy()
        pulse_shape = Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)
        node = chip.get_node_from_qubit_idx(idx=qubit_idx, readout=True)
        port = chip.get_port(node)
        old_time = self._update_time(
            time=time,
            qubit_idx=qubit_idx,
            pulse_time=gate_settings.duration + self.settings.delay_before_readout,
        )

        return (
            PulseEvent(
                pulse=Pulse(
                    amplitude=gate_settings.amplitude,
                    phase=gate_settings.phase,
                    duration=gate_settings.duration,
                    frequency=node.frequency,
                    pulse_shape=pulse_shape,
                ),
                start_time=old_time + self.settings.delay_before_readout,
            )
            if gate_settings.duration > 0
            else None,
            port,
        )

    def _parse_check_cz(self, cz: CZ):
        """Checks that given CZ qubits are supported by the hardware (defined in the runcard).
        Switches CZ(q1,q2) to CZ(q2,q1) if the former is not supported but the later is (note that CZ is symmetric)

        Args:
            cz (CZ): qibo CZ gate

        Returns:
            CZ: qibo CZ gate
        """

        cz_qubits = cz.qubits
        cz_from_settings = [qubit for qubit in self.settings.gates.keys() if isinstance(qubit, tuple)]
        if cz_qubits in cz_from_settings:
            return cz
        elif cz_qubits[::-1] in cz_from_settings:
            cz_qubits = cz_qubits[::-1]
            return CZ(cz_qubits[0], cz_qubits[1])
        else:
            raise NotImplementedError(f"CZ not defined for qubits {cz_qubits}")

    def _get_gate_settings_with_master_values(self, gate: Gate):
        """get gate settings with master values

        Args:
            gate (Gate): qibo / native gate

        Returns:
            gate_settings ()
        """
        gate_settings = HardwareGateFactory.gate_settings(
            gate=gate,
            master_amplitude_gate=self.settings.master_amplitude_gate,
            master_duration_gate=self.settings.master_duration_gate,
        )

        # check if duration is an integer value (admit floats with null decimal part)
        gate_duration = gate_settings.duration
        if not isinstance(gate_duration, int):  # this handles floats but also settings reading int as np.int64
            if gate_duration % 1 != 0:  # check decimals
                raise ValueError(
                    f"The settings of the gate {gate.name} have a non-integer duration ({gate_duration}ns). The gate duration must be an integer or a float with 0 decimal part"
                )
            else:
                gate_duration = int(gate_duration)

        return gate_settings

    def _update_time(self, time: dict[int, int], qubit_idx: int, pulse_time: int):
        """Create new timeline if not already created and update time.

        Args:
            time (Dict[int, int]): Dictionary with the time of each qubit.
            qubit_idx (int): Index of the qubit.
            pulse_time (int): Duration of the puls + wait time.
        """
        if qubit_idx not in time:
            time[qubit_idx] = 0
        old_time = time[qubit_idx]
        residue = pulse_time % self.settings.minimum_clock_time
        if residue != 0:
            pulse_time += self.settings.minimum_clock_time - residue
        time[qubit_idx] += pulse_time
        return old_time

    def _instantiate_gates_from_settings(self):
        """Instantiate all gates defined in settings and add them to the factory."""
        for qubits, gate_settings_list in list(self.settings.gates.items()):
            # parse string tupples for 2 qubit keys
            if isinstance(qubits, str):
                qubit_str = qubits
                qubits = ast.literal_eval(qubit_str)
                # check for expected output
                assert isinstance(qubits, tuple) and list(map(type, qubits)) == [int, int]
                self.settings.gates[qubits] = self.settings.gates.pop(qubit_str)
            for gate_settings in gate_settings_list:
                settings_dict = asdict(gate_settings)
                gate_class = HardwareGateFactory.get(name=settings_dict.pop(RUNCARD.NAME))
                if not gate_class.settings:
                    gate_class.settings = {}
                gate_class.settings[qubits] = gate_class.HardwareGateSettings(**settings_dict)
