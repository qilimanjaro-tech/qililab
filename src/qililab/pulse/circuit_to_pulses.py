"""Class that translates a Qibo Circuit into a PulseSequence"""
import ast
import contextlib
from dataclasses import asdict

from qibo.gates import CZ, Gate, M
from qibo.models.circuit import Circuit

from qililab.chip.nodes import Coupler, Qubit, Resonator
from qililab.config import logger
from qililab.constants import RUNCARD
from qililab.platform import Bus, Platform
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.settings.gate_settings import CircuitPulseSettings
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
            time: dict[str, int] = {}  # restart time
            for gate in circuit.queue:
                # Measurement gates need to be handled on their own because qibo allows to define
                # an M gate as eg. gates.M(*range(5))
                if isinstance(gate, M):
                    self._measurement_gate_to_pulses(gate, time=time, pulse_schedule=pulse_schedule)

                # handle wait gates
                elif isinstance(gate, qibo_gates.Wait):
                    self._update_time(time=time, target=gate.qubits[0], gate_time=gate.parameters[0])

                # handle control gates
                else:
                    # parse symmetry in CZ gates
                    if isinstance(gate, CZ):
                        gate = self._parse_check_cz(gate)

                    self._control_gate_to_pulses(gate, time=time, pulse_schedule=pulse_schedule)

            # TODO: what is this
            # for qubit in chip.qubits:
            #     with contextlib.suppress(ValueError):
            #         # If we find a flux port, create empty schedule for that port
            #         flux_port = chip.get_port_from_qubit_idx(idx=qubit, line=Line.FLUX)
            #         if flux_port is not None:
            #             pulse_schedule.create_schedule(port=flux_port)

            pulse_schedule_list.append(pulse_schedule)

        return pulse_schedule_list

    # TODO: simplify further measurement and control to unify code
    def _measurement_gate_to_pulses(self, gate: Gate, time: dict[str, int], pulse_schedule: PulseSchedule):
        for qubit_idx in gate.target_qubits:
            # get measurement schedule for relevant qubit
            m_gate = M(qubit_idx)
            gate_event = self._gate_schedule_from_settings(m_gate)[0]
            # find bus
            bus = self.platform.get_bus_by_alias(gate_event.bus)
            # update time
            start_time = self._update_time(time=time, target=bus.targets[0].alias, gate_time=gate_event.duration)
            # add pulse event
            pulse_event = self._circuit_pulse_to_pulse_event(time=start_time, gate=m_gate, gate_event=gate_event, bus=bus)
            pulse_schedule.add_event(pulse_event=pulse_event, port=bus.port, port_delay=bus.settings.delay)  # type: ignore

    def _control_gate_to_pulses(self, gate: Gate, time: dict[str, int], pulse_schedule: PulseSchedule):
        # extract gate schedule
        gate_schedule = self._gate_schedule_from_settings(gate)
        # get total duration for the gate
        gate_time = self._get_total_schedule_duration(gate_schedule)
        gate_qubits = self._get_gate_qubits(gate, gate_schedule)
        # update time, start time is that of the qubit most ahead in time
        start_time = 0
        for qubit in gate_qubits:
            start_time = max(self._update_time(time=time, target=qubit, gate_time=gate_time), start_time)
        # sync gate end time
        self._sync_qubit_times(gate_qubits, time=time)
        # apply gate schedule
        for gate_event in gate_schedule:
            # find bus
            bus = self.platform.get_bus_by_alias(gate_event.bus)
            # add control gate schedule
            pulse_event = self._circuit_pulse_to_pulse_event(time=start_time, gate=gate, gate_event=gate_event, bus=bus)
            # add event
            pulse_schedule.add_event(pulse_event=pulse_event, port=bus.port, port_delay=bus.settings.delay)  # type: ignore

    def _gate_schedule_from_settings(self, gate: Gate) -> list[CircuitPulseSettings]:
        """Get the gate schedule. The gate schedule is the list of pulses to apply
        to a given bus for a given gate

        Args:
            gate (Gate): Qibo gate

        Returns:
            list[CircuitPulseSettings]: schedule list with each of the pulses settings
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
            runcard_gate = next((gate for gate in self.runcard_gate_settings[qubits] if gate.name == name), None)
            if runcard_gate is None:
                raise NotImplementedError(
                    f"Did not find definition in runcard for circuit gate {gate.name} corresponding to HardwareGate {hardware_gate.name}"
                )
            return hardware_gate.translate(gate=gate, gate_schedule=runcard_gate.schedule)

        # allow "arbitrary" gates as long as they are defined in the runcard
        for runcard_gate in self.runcard_gate_settings[qubits]:
            if gate.name == runcard_gate.name:
                # raise warning
                logger.warning(f"Using arbitrary with name {runcard_gate.name} for qubits {qubits}")
                return runcard_gate.schedule

        raise NameError(f"Did not find gate settings for gate {gate.name} at qubits {qubits}")

    def _get_total_schedule_duration(self, schedule: list[CircuitPulseSettings]) -> int:
        """Return total time for a gate schedule. This is done by taking the max of (init + duration)
        for all the elements in the schedule

        Args:
            schedule (list[CircuitPulseSettings]): Schedule of pulses to apply

        Returns:
            int: Total gate time
        """
        time = 0
        for schedule_element in schedule:
            time = max(time, schedule_element.duration + schedule_element.wait_time)
        return time

    def _get_gate_qubits(self, gate: Gate, schedule: list[CircuitPulseSettings]) -> list[str]:
        """Get qubits involved in gate
        # TODO: also gets couplers

        Args:
            schedule (list[CircuitPulseSettings]): Gate schedule

        Returns:
            list[int]: list of qubits
        """

        schedule_qubits = [
            self.platform.get_bus_by_alias(schedule_element.bus).targets[0].alias for schedule_element in schedule
        ]
        gate_qubits = [
            f"qubit_{qubit}" for qubit in gate.qubits if qubit not in schedule_qubits
        ]  # TODO: i dont like this parsing, it's too hidden
        return schedule_qubits + gate_qubits

    def _circuit_pulse_to_pulse_event(self, time: int, gate: Gate, gate_event: CircuitPulseSettings, bus: Bus) -> PulseEvent:
        """Translate a gate into a pulse.

        Args:
            time (dict[int, int]): dictionary containing qubit indices as keys and current time (ns) as values
            readout_gate (Gate): measurement gate
            qubit_id (int): qubit number (note that the first qubit is the 0th).

        Returns:
            tuple[PulseEvent | None, int]: (PulseEvent or None, port_id).
        """

        shape_settings = gate_event.shape.copy()
        pulse_shape = Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)
        # TODO: save for future
        # targets = [node for node in bus.targets if isinstance(node, (Qubit, Coupler, Resonator))]
        # if all((isinstance(target, Resonator) for target in targets)): # handle resonators
        #     # TODO: look for a method to make this parsing better
        #     target = [res for res in targets if res.alias == f"resonator_q{gate.qubits[0]}"][0]
        # elif len(targets) > 1:
        #     raise ValueError(f"Found more than one target for {gate_event.bus}")
        # target = targets[0]
        return PulseEvent(
            pulse=Pulse(
                amplitude=gate_event.amplitude,
                phase=gate_event.phase,
                duration=gate_event.duration,
                frequency=gate_event.frequency,  # TODO: if we dont want to use node info we need to give the frequency somehow
                pulse_shape=pulse_shape,
            ),
            start_time=time + gate_event.wait_time + self.platform.settings.delay_before_readout,
            pulse_distortions=bus.distortions,
            qubit=gate.qubits[0],
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

    def _update_time(self, time: dict[str, int], target: str, gate_time: int):
        """Create new timeline if not already created and update time.

        Args:
            time (Dict[int, int]): Dictionary with the time of each qubit.
            qubit_idx (int): qubit index
            gate_time (int): total duration of the gate
        """
        if target not in time:
            time[target] = 0
        old_time = time[target]
        residue = (gate_time) % self.platform.settings.minimum_clock_time
        if residue != 0:
            gate_time += self.platform.settings.minimum_clock_time - residue
        time[target] += gate_time
        return old_time

    def _sync_qubit_times(self, qubits: list[str], time: dict[str, int]):
        """Syncs the time of the given qubit list

        Args:
            qubits (list[int]): qubits to sync
            time (dict[int,int]): time dictionary
        """
        max_time = max((time[qubit] for qubit in qubits if qubit in time), default=0)
        for qubit in qubits:
            time[qubit] = max_time
