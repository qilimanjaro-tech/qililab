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

"""CircuitToPulses class"""

from dataclasses import asdict

import numpy as np
from qibo import gates
from qibo.models import Circuit

from qililab.constants import RUNCARD
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings
from qililab.settings.digital.gate_event_settings import GateEventSettings
from qililab.typings.enums import Line
from qililab.utils import Factory

from .native_gates import Drag, Wait


class CircuitToPulses:
    """Translates circuits into pulse sequences."""

    def __init__(self, digital_compilation_settings: DigitalCompilationSettings):  # type: ignore # ignore typing to avoid importing platform and causing circular imports
        self.digital_compilation_settings = digital_compilation_settings

    def run(self, circuit: Circuit) -> PulseSchedule:
        """Translates a circuit into a  pulse sequences.

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

        pulse_schedule: PulseSchedule = PulseSchedule()
        time: dict[int, int] = {}  # init/restart time
        for gate in circuit.queue:
            # handle wait gates
            if isinstance(gate, Wait):
                self._update_time(time=time, qubit=gate.qubits[0], gate_time=gate.parameters[0])
                continue

            # Measurement gates need to be handled on their own because qibo allows to define
            # an M gate as eg. gates.M(*range(5))
            if isinstance(gate, gates.M):
                gate_schedule = []
                gate_qubits = gate.qubits
                for qubit in gate_qubits:
                    gate_schedule += self._gate_schedule_from_settings(gates.M(qubit))

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
                if isinstance(gate, gates.M):
                    gate = gates.M(*gate.qubits[1:])
                # add event
                delay = self.digital_compilation_settings.buses[gate_event.bus].delay
                pulse_schedule.add_event(pulse_event=pulse_event, bus_alias=gate_event.bus, delay=delay)  # type: ignore

        for bus_alias in self.digital_compilation_settings.buses:
            # If we find a flux port, create empty schedule for that port.
            # This is needed because for Qblox instrument working in flux buses as DC sources, if we don't
            # add an empty schedule its offsets won't be activated and the results will be misleading.
            if self.digital_compilation_settings.buses[bus_alias].line == Line.FLUX:
                pulse_schedule.create_schedule(bus_alias=bus_alias)

        return pulse_schedule

    def _gate_schedule_from_settings(self, gate: gates.Gate) -> list[GateEventSettings]:
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

    @staticmethod
    def _normalize_angle(angle: float):
        """Normalizes angle in range [-pi, pi].

        Args:
            angle (float): Normalized angle.
        """
        angle %= 2 * np.pi
        if angle > np.pi:
            angle -= 2 * np.pi
        return angle

    @staticmethod
    def _get_total_schedule_duration(schedule: list[GateEventSettings]) -> int:
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

    def _get_gate_qubits(self, gate: gates.Gate, schedule: list[GateEventSettings] | None = None) -> tuple[int, ...]:
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

    def _gate_element_to_pulse_event(self, time: int, gate: gates.Gate, gate_event: GateEventSettings) -> PulseEvent:
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
            if isinstance(gate, gates.M)
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

    @staticmethod
    def _sync_qubit_times(qubits: list[int], time: dict[int, int]):
        """Syncs the time of the given qubit list

        Args:
            qubits (list[int]): qubits to sync
            time (dict[int, int]): time dictionary
        """
        max_time = max((time[qubit] for qubit in qubits if qubit in time), default=0)
        for qubit in qubits:
            time[qubit] = max_time
