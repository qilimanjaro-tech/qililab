"""Class that translates a Qibo Circuit into a PulseSequence"""
import ast
import warnings
from dataclasses import asdict, dataclass

import numpy as np
from qibo.gates import CZ, Gate, M
from qibo.models.circuit import Circuit

from qililab.chip import Chip
from qililab.chip.nodes import Port, Qubit
from qililab.config import logger
from qililab.constants import RUNCARD
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.settings import RuncardSchema
from qililab.transpiler import Drag, Park
from qililab.utils import Factory


@dataclass  # TODO do we actually need this?
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

            for gate in circuit.queue:
                if not isinstance(gate, M):
                    # if gate is CZ, parse input to check for symmetric gates
                    # if gate is CZ, check if parking is needed
                    if isinstance(gate, CZ):
                        gate = self._parse_check_cz(gate)

                        # get qubits to park
                        park_qubits = self._get_parking_targets(gate, chip)
                        if len(park_qubits) != 0:
                            pad_times = []
                            for qubit in park_qubits:
                                park_gate_settings = [
                                    settings_gate
                                    for settings_gate in self.settings.gates[qubit]
                                    if "Park" in settings_gate.name
                                ]
                                if len(park_gate_settings) == 0:
                                    logger.warning(
                                        f"Found parking candidate qubit {qubit} for {gate.name} at qubits {gate.qubits} but did not find settings for parking gate at qubit {qubit}"
                                    )
                                    continue
                                cz_gate_settings = [
                                    settings_gate
                                    for settings_gate in self.settings.gates[gate.qubits]
                                    if "CZ" in settings_gate.name
                                ][0]

                                # get pad time
                                pad_time = self._get_park_pad_time(
                                    park_settings=park_gate_settings[0], cz_settings=cz_gate_settings
                                )
                                if pad_time % 1 != 0 or pad_time < 0:
                                    raise ValueError(
                                        f"Value pad_time {pad_time} for park gate at {qubit} and CZ {gate.qubits} has nonzero decimal or is negative"
                                    )
                                pad_times.append(int(pad_time))

                                # add parking gate
                                parking_gate = Park(qubit)
                                pulse_event, port = self._control_gate_to_pulse_event(
                                    time=time, control_gate=parking_gate, chip=chip
                                )
                                pulse_schedule.add_event(pulse_event=pulse_event, port=port)

                            # add padd time to CZ target qubit to sync it with parking gate
                            # if there is more than 1 pad time, add max (this is a bit misleading)
                            self._update_time(
                                time=time, qubit_idx=gate.target_qubits[0], pulse_time=max(pad_times, default=0)
                            )
                    # add control gate to pulse sequence
                    pulse_event, port = self._control_gate_to_pulse_event(time=time, control_gate=gate, chip=chip)
                    if pulse_event is not None:  # TODO check pulse event should not be None?
                        pulse_schedule.add_event(pulse_event=pulse_event, port=port)

                else:
                    # handle measurement gates
                    for qubit_idx in gate.target_qubits:
                        m_gate = M(qubit_idx)
                        readout_pulse_event, port = self._readout_gate_to_pulse_event(
                            time=time, readout_gate=m_gate, qubit_idx=qubit_idx, chip=chip
                        )
                        if readout_pulse_event is not None:
                            pulse_schedule.add_event(pulse_event=readout_pulse_event, port=port)

            pulse_schedule_list.append(pulse_schedule)

        return pulse_schedule_list

    def _get_park_pad_time(
        self,
        park_settings: RuncardSchema.PlatformSettings.GateSettings,
        cz_settings: RuncardSchema.PlatformSettings.GateSettings,
    ):
        """Gets pad time for parking gate

        Args:
            park_settings (HardwareGate.HardwareGateSettings): settings for the parking gate
            cz_settings (HardwareGate.HardwareGateSettings): settings for the cz gate for which we need parking

        Returns:
            pad_time (int): pad time

        Pad time is the extra time for the pulses on the parked qubits before and afer the snz pulse for the
        CZ gate is applied
        """

        # ideally pad time would be at Park gate definition
        # TODO find out why mypy complains about the line below
        # pad_time = (park_settings.duration - 2 * cz_settings.duration + 2 + cz_settings.shape["t_phi"]) / 2
        t_park = int(park_settings.duration)
        t_cz = int(cz_settings.duration)
        t_phi = int(cz_settings.shape["t_phi"])
        pad_time = (t_park - 2 * t_cz + 2 + t_phi) / 2

        return pad_time

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
        # for CZs check if they are possible (defined at runcard) and switch target if needed
        if isinstance(control_gate, CZ):
            control_gate = self._parse_check_cz(control_gate)

        qubit_idx = control_gate.target_qubits[0]
        node = chip.get_node_from_qubit_idx(idx=qubit_idx, readout=False)

        # TODO implement this inside chip class
        # get ports and select those we need
        adj_nodes = chip._get_adjacent_nodes(node)
        # get adjacent flux line (drive line) for CZ,Park gates (all others)
        if isinstance(control_gate, (CZ, Park)):
            line = "flux_line_q"
        else:
            line = "drive_line_q"

        # initialize variable port (ensure to get the error below if no port assigned)
        port = None
        for adj_node in adj_nodes:
            # check that first part of alias matches line name
            # note that aliases are usually eg. flux line for qubit 1 -> flux_line_q1
            if isinstance(adj_node, Port) and adj_node.alias == line + str(qubit_idx):
                port = adj_node

        if not isinstance(port, Port):
            raise RuntimeError(
                f"Wrong or no port found of type {line+str(qubit_idx)} for gate {control_gate.name} and qubit {qubit_idx} with node id {node.id_}"
            )

        # get amplitude from gate settings
        amplitude = float(gate_settings.amplitude)

        # check that phase is empty for Drag, CZ, Park
        # also handle specific gate settings
        if isinstance(control_gate, (Drag, CZ, Park)):
            # phase should be None
            phase = gate_settings.phase
            if gate_settings.phase is not None:
                raise ValueError(f"{control_gate.name} gate should not have setting for phase")

            # load amplitude, phase for drag pulse from circuit gate parameters
            if isinstance(control_gate, Drag):
                amplitude = (control_gate.parameters[0] / np.pi) * amplitude
                phase = control_gate.parameters[1]

        else:
            phase = float(gate_settings.phase)

        if isinstance(control_gate, CZ):
            # SNZ duration at gate settings is the SNZ halfpulse duration
            # should not use pulse duration interchangeably with gate duration
            cz_duration = 2 * gate_settings.duration + 2 + gate_settings.shape["t_phi"]
            old_time = self._update_2q_time(
                time=time,
                qubit_idx=control_gate.qubits,
                pulse_time=cz_duration + self.settings.delay_between_pulses,
            )

        else:
            old_time = self._update_time(
                time=time,
                qubit_idx=qubit_idx,
                pulse_time=gate_settings.duration + self.settings.delay_between_pulses,
            )

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
            port.id_,
        )

    def _get_parking_targets(self, cz: CZ, chip: Chip):
        """Gets targets for parking for the CZ's SNZ pulse

        Args:
            cz (CZ): CZ gate with qubits (control, target)
            chip (Chip): chip representation as a graph.

        Returns:
            qubit list[int]: list of qubit indices to be parked

        Qubits to be parked are those that are adjacent to the target qubit, are not the control qubit
        and have lower frequency than the target
        """
        target = cz.target_qubits[0]
        node = chip.get_node_from_qubit_idx(idx=target, readout=False)
        # get adjacent nodes
        adj_nodes = chip._get_adjacent_nodes(node)
        # return adjacent qubits not in CZ gate
        return [
            adj_node.qubit_index
            for adj_node in adj_nodes
            if isinstance(adj_node, Qubit)
            and adj_node.qubit_index not in cz.qubits
            and adj_node.frequency < node.frequency
        ]

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
        # gets resonator port
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
        two_qubit_gates = [qubit for qubit in self.settings.gates.keys() if isinstance(qubit, tuple)]
        if cz_qubits in two_qubit_gates:
            return cz
        elif cz_qubits[::-1] in two_qubit_gates:
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
            qubit_idx (int | tuple[int,int]): Index of the qubit or index of 2 qubits for 2 qubit gates.
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

    def _update_2q_time(self, time: dict[int, int], qubit_idx: tuple[int, int], pulse_time: int):
        """Create new timeline if not already created and update time.

        Args:
            time (Dict[int, int]): Dictionary with the time of each qubit.
            qubit_idx (tuple[int,int]): Index of the 2 qubit gate.
            pulse_time (int): Duration of the puls + wait time.
        """

        # get max time if existing, otherwise initialize both times
        max_time = max((time[qubit] for qubit in time if qubit in qubit_idx), default=0)
        if max_time == 0:
            time[qubit_idx[0]] = 0
            time[qubit_idx[1]] = 0

        old_time = max_time
        residue = pulse_time % self.settings.minimum_clock_time
        if residue != 0:
            pulse_time += self.settings.minimum_clock_time - residue

        # update time for both qubits / create dict entry if not created
        time[qubit_idx[0]] = max_time + pulse_time
        time[qubit_idx[1]] = max_time + pulse_time
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
