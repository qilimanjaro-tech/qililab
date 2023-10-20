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

"""Class that translates a Qibo Circuit into a PulseSequence"""
import contextlib
from dataclasses import asdict

import numpy as np
from qibo.gates import Gate, M
from qibo.models.circuit import Circuit

from qililab.chip.nodes import Coupler, Qubit
from qililab.constants import RUNCARD
from qililab.instruments import AWG
from qililab.platform import Bus, Platform
from qililab.settings.gate_event_settings import GateEventSettings
from qililab.transpiler import Drag
from qililab.typings.enums import Line
from qililab.utils import Factory, qibo_gates

from .pulse import Pulse
from .pulse_event import PulseEvent
from .pulse_schedule import PulseSchedule


class CircuitToPulses:  # pylint: disable=too-few-public-methods
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

    Arguments:
        platform (Platform): :class:`Platform` with gate and hardware settings

    Attributes:
        platform (Platform): same as above
    """

    def __init__(self, platform: Platform):
        self.platform = platform

    def translate(  # pylint: disable=too-many-locals, too-many-branches
        self, circuits: list[Circuit]
    ) -> list[PulseSchedule]:
        """Translates each circuit to a PulseSequences class, which is a list of PulseSequence classes for
        each different port and pulse name (control/readout).

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
                if isinstance(gate, qibo_gates.Wait):
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
                    # find bus
                    bus = self.platform._get_bus_by_alias(gate_event.bus)  # pylint: disable=protected-access
                    # add control gate schedule
                    pulse_event = self._gate_element_to_pulse_event(
                        time=start_time, gate=gate, gate_event=gate_event, bus=bus
                    )
                    # pop first qubit from gate if it is measurement
                    # this is so that the target qubit for multiM gates is every qubit in the M gate
                    if isinstance(gate, M):
                        gate = M(*gate.qubits[1:])
                    # add event
                    pulse_schedule.add_event(pulse_event=pulse_event, port=bus.port, port_delay=bus.settings.delay)  # type: ignore

            for qubit in self.platform.chip.qubits:
                with contextlib.suppress(ValueError):
                    # If we find a flux port, create empty schedule for that port
                    flux_port = self.platform.chip.get_port_from_qubit_idx(idx=qubit, line=Line.FLUX)
                    if flux_port is not None:
                        flux_bus = next((bus for bus in self.platform.buses if bus.port == flux_port), None)
                        if flux_bus and any(
                            isinstance(instrument, AWG) for instrument in flux_bus.system_control.instruments
                        ):
                            pulse_schedule.create_schedule(port=flux_port)

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

        gate_schedule = self.platform.gates_settings.get_gate(name=gate.__class__.__name__, qubits=gate.qubits)

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
        theta = self.normalize_angle(angle=gate.parameters[0])
        amplitude = drag_schedule.pulse.amplitude * theta / np.pi
        phase = self.normalize_angle(angle=gate.parameters[1])
        if amplitude < 0:
            amplitude = -amplitude
            phase = self.normalize_angle(angle=gate.parameters[1] + np.pi)
        drag_schedule.pulse.amplitude = amplitude
        drag_schedule.pulse.phase = phase
        return [drag_schedule]

    def normalize_angle(self, angle: float):
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

    def _get_gate_qubits(self, gate: Gate, schedule: list[GateEventSettings] | None = None) -> list[int]:
        """Gets qubits involved in gate. This includes gate.qubits but also qubits which are targets of
        buses in the gate schedule

        Args:
            schedule (list[CircuitPulseSettings]): Gate schedule

        Returns:
            list[int]: list of qubits
        """

        schedule_qubits = (
            [
                target.qubit_index
                for schedule_element in schedule
                for target in self.platform._get_bus_by_alias(  # pylint: disable=protected-access
                    schedule_element.bus
                ).targets
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
        if isinstance(gate, M):
            qubit = gate.qubits[0]
        # for couplers we don't need to set the target qubit
        elif isinstance(bus.targets[0], Coupler):
            qubit = None
        # handle control gates, target should be the qubit target of the bus
        else:
            qubit = next(target.qubit_index for target in bus.targets if isinstance(target, Qubit))

        return PulseEvent(
            pulse=Pulse(
                amplitude=pulse.amplitude,
                phase=pulse.phase,
                duration=pulse.duration,
                frequency=0,
                pulse_shape=pulse_shape,
            ),
            start_time=time + gate_event.wait_time + self.platform.gates_settings.delay_before_readout,
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
        residue = (gate_time) % self.platform.gates_settings.minimum_clock_time
        if residue != 0:
            gate_time += self.platform.gates_settings.minimum_clock_time - residue
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
