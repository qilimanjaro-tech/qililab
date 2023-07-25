"""Class that translates a Qibo Circuit into a PulseSequence"""
import ast
import contextlib
from dataclasses import asdict

from qibo.gates import CZ, Gate, M
from qibo.models.circuit import Circuit

from qililab.config import logger
from qililab.constants import RUNCARD
from qililab.platform import Platform
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.utils import Factory, qibo_gates


class CircuitToPulses:
    """Class that translates a Qibo Circuit into a PulseSequence"""

    def __init__(self, platform: Platform):
        self.platform = platform
        self.runcard_gate_settings = self.platform.settings.gates
        self.hardware_gates = HardwareGateFactory.pulsed_gates
        self.chip = self.platform.chip

    def translate(self, circuits: list[Circuit]) -> list[PulseSchedule]:
        """Translate each circuit to a PulseSequences class, which is a list of PulseSequence classes for
        each different port and pulse name (control/readout).

        Args:
            circuits (List[Circuit]): List of Qibo Circuit classes.

        Returns:
            list[PulseSequences]: List of PulseSequences classes.
        """
        pulse_schedule_list: list[PulseSchedule] = []
        for circuit in circuits:
            pulse_schedule = PulseSchedule()
            time: dict[int, int] = {}  # restart time
            for gate in circuit.queue:
                # Measurement gates need to be handled on their own because qibo allows to define
                # an M gate as eg. gates.M(*range(5))
                if isinstance(gate, M):
                    self._measurement_gate_to_pulses(gate, time=time, pulse_schedule=pulse_schedule)

                # handle wait gates
                elif isinstance(gate, qibo_gates.Wait):
                    self._update_time(time=time, qubit_idx=gate_qubits[0], gate_time=gate.parameters[0])

                # handle control gates
                else:
                    # parse symmetry in CZ gates
                    if isinstance(gate, CZ):
                        gate = self._parse_check_cz(gate)

                    # extract gate schedule
                    gate_schedule = self._gate_schedule_from_settings(gate)
                    # get total duration for the gate
                    gate_time = self._get_total_schedule_duration(gate_schedule)
                    gate_qubits = self._get_gate_qubits(gate, gate_schedule)
                    # update time, start time is that of the qubit most ahead in time
                    start_time = 0
                    for qubit in gate_qubits:
                        start_time = max(self._update_time(time=time, qubit_idx=qubit, gate_time=gate_time), start_time)
                    # sync gate end time
                    self._sync_qubit_times(gate_qubits, time=time)
                    # apply gate schedule
                    for circuit_pulse in gate_schedule:
                        # find bus
                        circuit_pulse.bus = self.platform.get_bus_by_alias(circuit_pulse.bus)
                        # add control gate schedule
                        pulse_event = self._schedule_element_to_pulse_event(
                            time=start_time, schedule_element=circuit_pulse
                        )
                        pulse_schedule.add_event(pulse_event=pulse_event, port=circuit_pulse.bus.port, port_delay=circuit_pulse.bus.settings.delay)  # type: ignore

            # TODO: what is this
            # for qubit in chip.qubits:
            #     with contextlib.suppress(ValueError):
            #         # If we find a flux port, create empty schedule for that port
            #         flux_port = chip.get_port_from_qubit_idx(idx=qubit, line=Line.FLUX)
            #         if flux_port is not None:
            #             pulse_schedule.create_schedule(port=flux_port)

            pulse_schedule_list.append(pulse_schedule)

        return pulse_schedule_list

    def _measurement_gate_to_pulses(self, gate: Gate, time: dict[int, int], pulse_schedule: PulseSchedule):
        for qubit_idx in gate.target_qubits:
            # get measurement schedule for relevant qubit
            m_gate = M(qubit_idx)
            circuit_pulse = self._gate_schedule_from_settings(m_gate)[0]
            # find bus
            circuit_pulse.bus = self.platform.get_bus_by_alias(circuit_pulse.bus)
            # update time
            start_time = self._update_time(time=time, qubit_idx=qubit_idx, gate_time=circuit_pulse.duration)
            # add pulse event
            pulse_event = self._schedule_element_to_pulse_event(time=start_time, schedule_element=circuit_pulse)
            pulse_schedule.add_event(pulse_event=pulse_event, port=circuit_pulse.bus.port, port_delay=circuit_pulse.bus.settings.delay)  # type: ignore

    def _gate_schedule_from_settings(self, gate: Gate) -> list[dict]:
        """Get the gate schedule. The gate schedule is the list of pulses to apply
        to a given bus for a given gate

        Args:
            gate (Gate): Qibo gate

        Returns:
            list[dict]: schedule list with each of the pulses settings
        """
        qubits = gate.qubits[0] if len(gate.qubits) == 1 else gate.qubits
        # check if gate in hardware gates
        name, hardware_gate = next(
            (
                (name, hardware_gate)
                for name, hardware_gate in self.hardware_gates.items()
                if isinstance(gate, hardware_gate.class_type)
            ),
            (None, None),
        )

        if hardware_gate is not None:
            runcard_gate = next(gate for gate in self.runcard_gate_settings[qubits] if gate.name == name)
            return hardware_gate.translate(
                gate=gate, gate_schedule=runcard_gate.schedule
            )  # TODO: use translate through HardwareGateSettings / make more roboust so that it doesnt resutn just a list[dict]

        # allow "arbitrary" gates as long as they are defined in the runcard
        for runcard_gate in self.runcard_gate_settings[qubits]:
            if gate.name == runcard_gate.name:
                # raise warning
                logger.warning(f"Using arbitrary with name {runcard_gate.name} for qubits {runcard_gate.qubits}")
                return runcard_gate.schedule

        raise NameError(f"Did not find gate settings for gate {gate.name} at qubits {gate.qubits}")

    def _get_total_schedule_duration(self, schedule: list[dict]) -> int:
        """Return total time for a gate schedule. This is done by taking the max of (init + duration)
        for all the elements in the schedule

        Args:
            schedule (list[dict]): Schedule of pulses to apply

        Returns:
            int: Total gate time
        """
        time = 0
        for schedule_element in schedule:
            time = max(time, schedule_element.duration + schedule_element.wait_time)
        return time

    def _get_gate_qubits(self, gate: Gate, schedule: list[dict]) -> list[int]:
        """Get qubits involved in gate

        Args:
            schedule (list[dict]): Gate schedule

        Returns:
            list[int]: list of qubits
        """
        schedule_qubits = [schedule_element.qubit for schedule_element in schedule]
        gate_qubits = [qubit for qubit in gate.qubits if qubit not in schedule_qubits]
        return schedule_qubits + gate_qubits

    def _schedule_element_to_pulse_event(self, time: int, schedule_element: dict) -> PulseEvent:
        """Translate a gate into a pulse.

        Args:
            time (dict[int, int]): dictionary containing qubit indices as keys and current time (ns) as values
            readout_gate (Gate): measurement gate
            qubit_id (int): qubit number (note that the first qubit is the 0th).

        Returns:
            tuple[PulseEvent | None, int]: (PulseEvent or None, port_id).
        """

        shape_settings = schedule_element.shape.copy()
        pulse_shape = Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)
        bus = schedule_element.bus

        return PulseEvent(
            pulse=Pulse(
                amplitude=schedule_element.amplitude,
                phase=schedule_element.phase,
                duration=schedule_element.duration,
                frequency=schedule_element.frequency,  # TODO: if we dont want to use node info we need to give the frequency somehow
                pulse_shape=pulse_shape,
            ),
            start_time=time + schedule_element.wait_time + self.platform.settings.delay_before_readout,
            pulse_distortions=bus.distortions,
            qubit=schedule_element.qubit,
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

    def _update_time(self, time: dict[int, int], qubit_idx: int, gate_time: int):
        """Create new timeline if not already created and update time.

        Args:
            time (Dict[int, int]): Dictionary with the time of each qubit.
            qubit_idx (int): qubit index
            gate_time (int): total duration of the gate
        """
        if qubit_idx not in time:
            time[qubit_idx] = 0
        old_time = time[qubit_idx]
        residue = (gate_time) % self.platform.settings.minimum_clock_time
        if residue != 0:
            gate_time += self.platform.settings.minimum_clock_time - residue
        time[qubit_idx] += gate_time
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
