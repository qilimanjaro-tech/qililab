"""Class that translates a Qibo Circuit into a PulseSequence"""
import ast
import contextlib
from dataclasses import asdict

from qibo.gates import CZ, Gate, M
from qibo.models.circuit import Circuit

from qililab.chip import Chip
from qililab.chip.nodes import Qubit
from qililab.config import logger
from qililab.constants import RUNCARD
from qililab.platform import Platform
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.settings import RuncardSchema
from qililab.transpiler import Park
from qililab.typings.enums import Line
from qililab.utils import Factory, qibo_gates


class CircuitToPulses:
    """Class that translates a Qibo Circuit into a PulseSequence"""

    def __init__(self, platform: Platform):
        self.platform = platform
        self._instantiate_gates_from_settings()

    def translate(self, circuits: list[Circuit]) -> list[PulseSchedule]:
        """Translate each circuit to a PulseSequences class, which is a list of PulseSequence classes for
        each different port and pulse name (control/readout).

        Args:
            circuits (List[Circuit]): List of Qibo Circuit classes.
            chip (Chip): Chip representation as a graph.

        Returns:
            list[PulseSequences]: List of PulseSequences classes.
        """
        chip = self.platform.chip
        pulse_schedule_list: list[PulseSchedule] = []
        for circuit in circuits:
            pulse_schedule = PulseSchedule()
            time: dict[int, int] = {}  # restart time
            for gate in circuit.queue:
                if isinstance(gate, qibo_gates.Wait):
                    self._update_time(time, gate.target_qubits[0], gate.parameters[0])
                    continue
                elif isinstance(gate, M):
                    # handle measurement gates
                    for qubit_idx in gate.target_qubits:
                        m_gate = M(qubit_idx)
                        readout_pulse_event, port = self._readout_gate_to_pulse_event(
                            time=time,
                            readout_gate=m_gate,
                            qubit_idx=qubit_idx,
                            chip=chip,
                        )
                        if readout_pulse_event is not None:
                            _, bus = self.platform.get_bus(port=port)
                            if bus is not None:
                                pulse_schedule.add_event(
                                    pulse_event=readout_pulse_event, port=port, port_delay=bus.settings.delay
                                )
                            with contextlib.suppress(ValueError):
                                # If we find a flux port, create empty schedule for that port
                                flux_port = chip.get_port_from_qubit_idx(idx=m_gate.target_qubits[0], line=Line.FLUX)
                                if flux_port is not None:
                                    pulse_schedule.create_schedule(port=flux_port)
                    continue

                elif isinstance(gate, CZ):
                    # CZ sends a SNZ pulse to target in CZ(control, target)
                    # handle parking and padding for CZ gates
                    gate = self._parse_check_cz(gate)
                    if (
                        chip.get_node_from_qubit_idx(idx=gate.target_qubits[0], readout=False).frequency
                        < chip.get_node_from_qubit_idx(idx=gate.control_qubits[0], readout=False).frequency
                    ):
                        raise ValueError(
                            f"Attempting to perform {gate.name} on qubits {gate.qubits} by targeting qubit {gate.target_qubits[0]} which has lower frequency than {gate.control_qubits[0]}"
                        )
                    parking_gates_pads = self._get_parking_gates(cz=gate, chip=chip)
                    # sync times for all qubits involved
                    cz_qubits = [gate.qubits[0] for gate, _ in parking_gates_pads]
                    cz_qubits.extend(gate.qubits)
                    self._sync_qubit_times(cz_qubits, time)

                    for parking_gate, _ in parking_gates_pads:
                        pulse_event, port = self._control_gate_to_pulse_event(
                            time=time,
                            control_gate=parking_gate,
                            chip=chip,
                        )
                        if pulse_event is not None:
                            _, bus = self.platform.get_bus(port=port)
                            if bus is not None:
                                pulse_schedule.add_event(
                                    pulse_event=pulse_event, port=port, port_delay=bus.settings.delay
                                )
                    # add padd time to CZ target qubit to sync it with parking gate
                    # if there is more than 1 pad time, add max (this is a bit misleading)
                    pad_time = max((time for _, time in parking_gates_pads), default=0)
                    if pad_time != 0:
                        self._update_time(
                            time=time,
                            qubit_idx=gate.target_qubits[0],
                            pulse_time=pad_time,
                        )

                # add control gates
                pulse_event, port = self._control_gate_to_pulse_event(time=time, control_gate=gate, chip=chip)
                # add pad time at the end of CZ to both target and control
                # note that we dont need to do this for the control qubit at the beginning of the pulse
                # since its time is already synced with the target qubit in _control_gate_to_pulse_event
                if isinstance(gate, CZ) and pad_time != 0:
                    self._update_time(time=time, qubit_idx=gate.target_qubits[0], pulse_time=pad_time)
                    self._update_time(time=time, qubit_idx=gate.control_qubits[0], pulse_time=pad_time)
                if pulse_event is not None:  # this happens for the Identity gate
                    _, bus = self.platform.get_bus(port=port)
                    if bus is not None:
                        pulse_schedule.add_event(pulse_event=pulse_event, port=port, port_delay=bus.settings.delay)

            for qubit in chip.qubits:
                with contextlib.suppress(ValueError):
                    # If we find a flux port, create empty schedule for that port
                    flux_port = chip.get_port_from_qubit_idx(idx=qubit, line=Line.FLUX)
                    if flux_port is not None:
                        pulse_schedule.create_schedule(port=flux_port)

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
        CZ gate is applied. Thus if a CZ duration is t_cz and its corresponding parking gate duration is t_p,
        pad time will be (t_p - t_cz) / 2 - this time will be allocated before and after the CZ's pulse
        """

        # ideally pad time would be at Park gate definition
        # TODO find out why mypy complains about the line below
        # pad_time = (park_settings.duration - 2 * cz_settings.duration + 2 + cz_settings.shape["t_phi"]) / 2
        t_park = int(park_settings.duration)
        t_cz = int(cz_settings.duration)
        if "t_phi" not in cz_settings.shape:
            return (t_park - t_cz) / 2
        t_phi = int(cz_settings.shape["t_phi"])
        return (t_park - (2 * t_cz + 2 + t_phi)) / 2

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
        """
        gate_settings = self._get_gate_settings(gate=control_gate)
        pulse_shape = self._build_pulse_shape_from_gate_settings(gate_settings=gate_settings)
        # for CZs check if they are possible (defined at runcard) and switch target if needed

        qubit_idx = control_gate.target_qubits[0]

        # get adjacent flux line (drive line) for CZ,Park gates (all others)
        node = chip.get_node_from_qubit_idx(idx=qubit_idx, readout=False)
        if isinstance(control_gate, (CZ, Park)):
            port = chip.get_port_from_qubit_idx(idx=control_gate.target_qubits[0], line=Line.FLUX)
        else:
            port = chip.get_port_from_qubit_idx(idx=control_gate.target_qubits[0], line=Line.DRIVE)

        # set frequency to 0 for CZ, park
        frequency = 0 if isinstance(control_gate, (CZ, Park)) else node.frequency

        # update time
        old_time = self._update_time(
            time=time,
            qubit_idx=qubit_idx,
            pulse_time=gate_settings.duration + self.platform.settings.delay_between_pulses,
        )

        if isinstance(control_gate, CZ):
            # sync control qubit time
            time[control_gate.control_qubits[0]] = time[control_gate.target_qubits[0]]

        _, bus = self.platform.get_bus(port=port)

        if bus is None:
            raise TypeError("bus cannot be None to get the distortions")

        return (
            PulseEvent(
                pulse=Pulse(
                    amplitude=float(gate_settings.amplitude),
                    phase=float(gate_settings.phase),
                    duration=gate_settings.duration,
                    pulse_shape=pulse_shape,
                    frequency=frequency,
                ),
                start_time=old_time,
                pulse_distortions=bus.distortions,
            )
            if gate_settings.duration > 0
            else None,
            port,
        )

    def _get_gate_settings(self, gate: Gate):
        """get gate setting values

        Args:
            gate (Gate): qibo / native gate

        Returns:
            gate_settings ()
        """
        gate_settings = HardwareGateFactory.gate_settings(gate=gate)
        # check if duration is an integer value (admit floats with null decimal part)
        gate_duration = gate_settings.duration
        if not isinstance(gate_duration, int):  # this handles floats but also settings reading int as np.int64
            if gate_duration % 1 != 0:  # check decimals
                raise ValueError(
                    f"The settings of the gate {gate.name} have a non-integer duration ({gate_duration}ns). "
                    "The gate duration must be an integer or a float with 0 decimal part"
                )
            else:
                gate_duration = int(gate_duration)

        return gate_settings

    def _get_parking_gates(self, cz: CZ, chip: Chip):
        """Gets parking gates for CZ's SNZ pulse

        Args:
            cz (CZ): CZ gate with qubits (control, target)
            chip (Chip): chip representation as a graph.

        Returns:
            list[int]: list of qubit indices to be parked


        Qubits to be parked are those that are adjacent to the target qubit, are not the control qubit
        and have lower frequency than the target.
        """

        # get parkable qubits
        target = cz.target_qubits[0]
        node = chip.get_node_from_qubit_idx(idx=target, readout=False)
        # get adjacent nodes
        adj_nodes = chip._get_adjacent_nodes(node)
        # return adjacent qubits with lower frequency than target not in CZ gate
        park_qubits = [
            adj_node.qubit_index
            for adj_node in adj_nodes
            if isinstance(adj_node, Qubit)
            and adj_node.qubit_index not in cz.qubits
            and adj_node.frequency < node.frequency
        ]

        park_gates = []
        # get qubits to park
        for qubit in park_qubits:
            park_gate_settings = [
                settings_gate for settings_gate in self.platform.settings.gates[qubit] if "Park" in settings_gate.name
            ]
            if not park_gate_settings:
                logger.warning(
                    f"Found parking candidate qubit {qubit} for {cz.name} at qubits {cz.qubits} but did not find settings for parking gate at qubit {qubit}"
                )
                continue
            cz_gate_settings = [
                settings_gate for settings_gate in self.platform.settings.gates[cz.qubits] if "CZ" in settings_gate.name
            ][0]

            # get pad time
            pad_time = self._get_park_pad_time(park_settings=park_gate_settings[0], cz_settings=cz_gate_settings)
            if pad_time < 0:
                raise ValueError(
                    f"Negative value pad_time {pad_time} for park gate at {qubit} and CZ {cz.qubits}. Pad time is calculated as (ParkGate.duration - CZ pulse duration) / 2"
                )

            park_gates.append((Park(qubit), int(pad_time)))

        return park_gates

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
        gate_settings = self._get_gate_settings(gate=readout_gate)
        shape_settings = gate_settings.shape.copy()
        pulse_shape = Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)
        node = chip.get_node_from_qubit_idx(idx=qubit_idx, readout=True)
        port = chip.get_port_from_qubit_idx(idx=qubit_idx, line=Line.FEEDLINE_INPUT)
        old_time = self._update_time(
            time=time,
            qubit_idx=qubit_idx,
            pulse_time=gate_settings.duration + self.platform.settings.delay_before_readout,
        )
        _, bus = self.platform.get_bus(port=port)

        if bus is None:
            raise TypeError("bus cannot be None to get the distortions")

        return (
            PulseEvent(
                pulse=Pulse(
                    amplitude=gate_settings.amplitude,
                    phase=gate_settings.phase,
                    duration=gate_settings.duration,
                    frequency=node.frequency,
                    pulse_shape=pulse_shape,
                ),
                start_time=old_time + self.platform.settings.delay_before_readout,
                pulse_distortions=bus.distortions,
                qubit=qubit_idx,
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
        two_qubit_gates = [qubit for qubit in self.platform.settings.gates.keys() if isinstance(qubit, tuple)]
        if cz_qubits in two_qubit_gates:
            return cz
        elif cz_qubits[::-1] in two_qubit_gates:
            return CZ(cz_qubits[1], cz_qubits[0])
        raise NotImplementedError(f"CZ not defined for qubits {cz_qubits}")

    def _update_time(self, time: dict[int, int], qubit_idx: int, pulse_time: int):
        """Create new timeline if not already created and update time.

        Args:
            time (Dict[int, int]): Dictionary with the time of each qubit.
            qubit_idx (int | tuple[int,int]): Index of the qubit or index of 2 qubits for 2 qubit gates.
            pulse_time (int): Duration of the pulse.
        """
        if qubit_idx not in time:
            time[qubit_idx] = 0
        old_time = time[qubit_idx]
        residue = (pulse_time) % self.platform.settings.minimum_clock_time
        if residue != 0:
            pulse_time += self.platform.settings.minimum_clock_time - residue
        time[qubit_idx] += pulse_time
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

    def _instantiate_gates_from_settings(self):
        """Instantiate all gates defined in settings and add them to the factory."""
        for qubits, gate_settings_list in list(self.platform.settings.gates.items()):
            # parse string tupples for 2 qubit keys
            if isinstance(qubits, str):
                qubit_str = qubits
                qubits = ast.literal_eval(qubit_str)
                # get tuple from string
                self.platform.settings.gates[qubits] = self.platform.settings.gates.pop(qubit_str)
            for gate_settings in gate_settings_list:
                settings_dict = asdict(gate_settings)
                gate_class = HardwareGateFactory.get(name=settings_dict.pop(RUNCARD.NAME))
                if not hasattr(gate_class, "settings"):
                    gate_class.settings = {}
                gate_class.settings[qubits] = gate_class.HardwareGateSettings(**settings_dict)
