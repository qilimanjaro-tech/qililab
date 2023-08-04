"""Class that translates a Qibo Circuit into a PulseSequence"""
import ast
import contextlib
from copy import copy
from dataclasses import asdict

import numpy as np
from qibo.gates import CZ, Gate, I, M
from qibo.models.circuit import Circuit

from qililab.chip.nodes import Coupler, Qubit, Resonator
from qililab.constants import RUNCARD
from qililab.platform import Bus, Platform
from qililab.pulse import PulseShape
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.settings.gate_settings import GateEventSettings
from qililab.transpiler import Drag
from qililab.utils import Factory, qibo_gates


class CircuitToPulses:
    """Class that translates a Qibo Circuit into a PulseSequence"""

    def __init__(self, platform: Platform):
        self.platform = platform
        self.runcard_gate_settings = self.platform.settings.gates
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
                    self._update_time(time=time, qubit=gate.qubits[0], gate_time=gate.parameters[0])
                # handle identity
                elif isinstance(gate, I):
                    continue
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
    def _measurement_gate_to_pulses(self, gate: Gate, time: dict[int, int], pulse_schedule: PulseSchedule):
        gate_qubits = self._get_gate_qubits(gate)
        # sync qubits
        self._sync_qubit_times(gate_qubits, time=time)
        for qubit_idx in gate.target_qubits:
            # get measurement schedule for relevant qubit
            m_gate = M(qubit_idx)
            gate_event = self._gate_schedule_from_settings(m_gate)[0]

            # find bus
            bus = self.platform.get_bus_by_alias(gate_event.bus)
            # update time
            start_time = self._update_time(time=time, qubit=m_gate.qubits[0], gate_time=gate_event.pulse.duration)

            # add pulse event
            pulse_event = self._gate_element_to_pulse_event(
                time=start_time, gate=m_gate, gate_event=gate_event, bus=bus
            )
            pulse_schedule.add_event(pulse_event=pulse_event, port=bus.port, port_delay=bus.settings.delay)  # type: ignore

    def _control_gate_to_pulses(self, gate: Gate, time: dict[int, int], pulse_schedule: PulseSchedule):
        # extract gate schedule
        gate_schedule = self._gate_schedule_from_settings(gate)
        # get total duration for the gate
        gate_time = self._get_total_schedule_duration(gate_schedule)
        gate_qubits = self._get_gate_qubits(gate, gate_schedule)
        # update time, start time is that of the qubit most ahead in time
        start_time = 0
        for qubit in gate_qubits:
            start_time = max(self._update_time(time=time, qubit=qubit, gate_time=gate_time), start_time)
        # sync gate end time
        self._sync_qubit_times(gate_qubits, time=time)
        # apply gate schedule
        for gate_event in gate_schedule:
            # find bus
            bus = self.platform.get_bus_by_alias(gate_event.bus)
            # add control gate schedule
            pulse_event = self._gate_element_to_pulse_event(time=start_time, gate=gate, gate_event=gate_event, bus=bus)
            # add event
            pulse_schedule.add_event(pulse_event=pulse_event, port=bus.port, port_delay=bus.settings.delay)  # type: ignore

    def _gate_schedule_from_settings(self, gate: Gate) -> list[GateEventSettings]:
        # sourcery skip: extract-method
        """Get the gate schedule. The gate schedule is the list of pulses to apply
        to a given bus for a given gate

        Args:
            gate (Gate): Qibo gate

        Returns:
            list[GateEventSettings]: schedule list with each of the pulses settings
        """

        gate_schedule = self.platform.settings.get_gate(name=gate.__class__.__name__, qubits=gate.qubits).schedule

        if not isinstance(gate, Drag):
            return gate_schedule

        # drag gate
        if len(gate_schedule) > 1:
            raise ValueError(
                f"Schedule for the drag gate is expected to have only 1 pulse but instead found {len(gate_schedule)} pulses"
            )
        drag_schedule = GateEventSettings(
            **asdict(gate_schedule[0])
        )  # make new object so that gate_schedule is not overwritten
        theta = self.normalize_angle(angle=gate.parameters[0])
        amplitude = drag_schedule.pulse.amplitude * theta / np.pi
        phase = self.normalize_angle(angle=gate.parameters[1])
        drag_schedule.pulse.amplitude = amplitude
        drag_schedule.pulse.phase = phase
        return [drag_schedule]

    def normalize_angle(self, angle: float):
        """Normalize angle in range [-pi, pi].

        Args:
            angle (float): Normalized angle.
        """
        angle %= 2 * np.pi
        if angle > np.pi:
            angle -= 2 * np.pi
        return angle

    def _get_total_schedule_duration(self, schedule: list[GateEventSettings]) -> int:
        """Return total time for a gate schedule. This is done by taking the max of (init + duration)
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

    def _get_gate_qubits(self, gate: Gate, schedule: list[GateEventSettings] | None = None) -> list[int]:
        """Get qubits involved in gate

        Args:
            schedule (list[CircuitPulseSettings]): Gate schedule

        Returns:
            list[int]: list of qubits
        """

        schedule_qubits = (
            [
                target.qubit_index
                for schedule_element in schedule
                for target in self.platform.get_bus_by_alias(schedule_element.bus).targets
                if isinstance(target, Qubit)
            ]
            if schedule is not None
            else []
        )

        gate_qubits = list(gate.qubits)

        return list(set(schedule_qubits + gate_qubits))  # converto to set and back to list to remove repeated items

    def _gate_element_to_pulse_event(
        self, time: int, gate: Gate, gate_event: GateEventSettings, bus: Bus
    ) -> PulseEvent:
        """Translate a gate into a pulse.

        Args:
            time (dict[int, int]): dictionary containing qubit indices as keys and current time (ns) as values
            readout_gate (Gate): measurement gate
            qubit_id (int): qubit number (note that the first qubit is the 0th).

        Returns:
            tuple[PulseEvent | None, int]: (PulseEvent or None, port_id).
        """

        # copy to avoid modifying runcard settings
        pulse = gate_event.pulse
        pulse_shape_copy = pulse.shape.copy()
        pulse_shape = Factory.get(pulse_shape_copy.pop(RUNCARD.NAME))(**pulse_shape_copy)

        # handle measurement gates and target qubits for control gates which might have multi-qubit schedules
        if all(isinstance(target, Resonator) for target in bus.targets):  # measurement gate
            qubit = gate.qubits[0]
        elif isinstance(bus.targets[0], Coupler):
            qubit = None
        else:
            qubit = next(target.qubit_index for target in bus.targets if isinstance(target, Qubit))

        return PulseEvent(
            pulse=Pulse(
                amplitude=pulse.amplitude,
                phase=pulse.phase,
                duration=pulse.duration,
                frequency=pulse.frequency,
                pulse_shape=pulse_shape,
            ),
            start_time=time + gate_event.wait_time + self.platform.settings.delay_before_readout,
            pulse_distortions=bus.distortions,
            qubit=qubit,
        )

    def _parse_check_cz(self, cz: CZ):
        """Checks if CZ is defined in the runcard, otherwise returns its symmetric gate (with flipped qubits)
        If none of those are defined in the runcard, a KeyError will be raised by platform.settings on trying
        to find the gate with qubits flipped

        Args:
            cz (CZ): qibo CZ gate

        Returns:
            CZ: qibo CZ gate
        """
        cz_qubits = cz.qubits
        try:
            self.platform.settings.get_gate(name=cz.__class__.__name__, qubits=cz_qubits)
            return cz
        except KeyError:
            return CZ(cz_qubits[1], cz_qubits[0])

    def _update_time(self, time: dict[int, int], qubit: int, gate_time: int):
        """Create new timeline if not already created and update time.

        Args:
            time (Dict[int, int]): Dictionary with the time of each qubit.
            qubit_idx (int): qubit index
            gate_time (int): total duration of the gate
        """
        if qubit not in time:
            time[qubit] = 0
        old_time = time[qubit]
        residue = (gate_time) % self.platform.settings.minimum_clock_time
        if residue != 0:
            gate_time += self.platform.settings.minimum_clock_time - residue
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
