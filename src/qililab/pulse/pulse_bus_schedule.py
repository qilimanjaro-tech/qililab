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

"""PulseBusSchedule class."""
from __future__ import annotations

from bisect import insort
from dataclasses import dataclass, field

import numpy as np

from qililab.constants import PULSEBUSSCHEDULE
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.utils import Waveforms


@dataclass
class PulseBusSchedule:
    """Container of Pulse objects addressed to the same bus.

    Args:
        port (str): Port (bus) alias.
        timeline (list[PulseEvent]): List of :class:`PulseEvent` objects the PulseBusSchedule is composed of.

    Examples:
        You can create a PulseBusSchedule targeting a bus or port in our chip by doing:

        .. code-block:: python3

            drag_pulse = Pulse(
                amplitude=1,
                phase=0.5,
                duration=200,
                frequency=1e9,
                pulse_shape=Drag(num_sigmas=4, drag_coefficient=0.5)
            )
            drag_pulse_event = PulseEvent(
                pulse=drag_pulse,
                start_time=0
            )

            drive_schedule = PulseBusSchedule(
                timeline=[drag_pulse_event],
                port="drive_q0"
            )

        You can add further pulse events to an already created PulseBusSchedule. To do so:

        .. code-block:: python3

            drag_pulse_0 = Pulse(
                amplitude=1,
                phase=0.5,
                duration=200,
                frequency=1e9,
                pulse_shape=Drag(num_sigmas=4, drag_coefficient=0.5)
            )
            drag_pulse_event = PulseEvent(
                pulse=drag_pulse_0,
                start_time=0
            )

            drive_schedule = PulseBusSchedule(
                timeline=[drag_pulse_event],
                port="drive_q0"
            )
            drag_pulse_1 = Pulse(
                amplitude=1,
                phase=0.5,
                duration=400,
                frequency=1e7,
                pulse_shape=Drag(num_sigmas=2, drag_coefficient=0.2)
            )
            drag_pulse_event_1 = PulseEvent(
                pulse=drag_pulse_1,
                start_time=204
            )
            drive_schedule.add_event(drag_pulse_event_1)
    """

    # FIXME: we may have one port being used by more than one bus. Use virtual ports instead.
    port: str  #: Port(bus) alias.
    timeline: list[PulseEvent] = field(
        default_factory=list
    )  #: List of PulseEvent objects the PulseBusSchedule is composed of.
    _pulses: set[Pulse] = field(init=False, default_factory=set)

    def __post_init__(self):
        """Sorts timeline and add used pulses to the pulses set if timeline is not empty."""
        if self.timeline:
            self.timeline.sort()
            for pulse_event in self.timeline:
                self._pulses.add(pulse_event.pulse)

    def add_event(self, pulse_event: PulseEvent):
        """Adds pulse event to sequence.

        Args:
            pulse_event (PulseEvent): :class:`PulseEvent` object.
        """
        self._pulses.add(pulse_event.pulse)
        insort(self.timeline, pulse_event)

    @property
    def end_time(self) -> int:
        """End of the PulseBusSchedule.

        Returns:
            int: End of the PulseBusSchedule."""
        end = 0
        for event in self.timeline:
            pulse_end = event.start_time + event.duration
            end = max(pulse_end, end)
        return end

    @property
    def start_time(self) -> int:
        """Start of the PulseBusSchedule.

        Returns:
            int: Start of the PulseBusSchedule."""
        return self.timeline[0].start_time

    @property
    def duration(self) -> int:
        """Duration of the PulseBusSchedule.

        Returns:
            int: Duration of the PulseBusSchedule."""
        return self.end_time - self.start_time

    @property
    def unique_pulses_duration(self) -> int:
        """Duration of the unique pulses, one immediately after the other.

        Returns:
            int: Duration of the unique pulses."""
        return sum(pulse.duration for pulse in self._pulses)

    @property
    def pulses(self):
        """Set of Pulse objects used in this PulseBusSchedule.

        Returns:
            str: The set of :class:`Pulse` objects."""
        return self._pulses

    @property
    def qubit(self):
        """Qubit index addressed by this PulseBusSchedule.

        Raises:
            ValueError: If more than one qubit is addressed by this PulseBusSchedule.

        Returns:
            int: The qubit index addressed by this PulseBusSchedule.
        """
        qubits = {pulse_event.qubit for pulse_event in self.timeline}
        if len(qubits) > 1:
            raise ValueError("More than one qubit is addressed by this PulseBusSchedule.")
        return qubits.pop()

    def __iter__(self):
        """Redirects __iter__ magic method."""
        return self.timeline.__iter__()

    def waveforms(self, resolution: float = 1.0, modulation: bool = True) -> Waveforms:
        """PulseBusSchedule 'waveforms' property.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Waveforms: Class containing the I, Q waveforms for a specific qubit.
        """
        waveforms = Waveforms()
        time = 0
        for pulse_event in self.timeline:
            wait_time = round((pulse_event.start_time - time) / resolution)
            if wait_time > 0:
                waveforms.add(imod=np.zeros(shape=wait_time), qmod=np.zeros(shape=wait_time))
            time += wait_time
            if modulation:
                pulse_waveforms = pulse_event.modulated_waveforms(resolution=resolution)
            else:
                real_env = np.real(pulse_event.envelope(resolution=resolution))
                imag_env = np.imag(pulse_event.envelope(resolution=resolution))
                pulse_waveforms = Waveforms(i=real_env, q=imag_env)
            waveforms += pulse_waveforms
            time += pulse_event.duration

        return waveforms

    def qubit_schedules(self) -> list[PulseBusSchedule]:
        """Separates all the :class:`PulseEvent` objects that act on different qubits, and returns a list
        of PulseBusSchedule objects, each one acting on a single qubit.

        Returns:
            list[PulseBusSchedule]: List of PulseBusSchedule objects, each one acting on a single qubit.
        """
        schedules = []
        qubits = {pulse_event.qubit for pulse_event in self.timeline}
        for qubit in qubits:
            schedule = PulseBusSchedule(
                port=self.port, timeline=[pulse_event for pulse_event in self.timeline if pulse_event.qubit == qubit]
            )
            schedules.append(schedule)
        return schedules

    def to_dict(self):
        """Returns dictionary representation of the class.

        Returns:
            dict: Dictionary representation of the class.
        """
        return {
            PULSEBUSSCHEDULE.TIMELINE: [pulse_event.to_dict() for pulse_event in self.timeline],
            PULSEBUSSCHEDULE.PORT: self.port,
        }

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Loads PulseBusSchedule object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseBusSchedule object.

        Returns:
            PulseBusSchedule: Loaded class.
        """
        timeline = [PulseEvent.from_dict(event) for event in dictionary[PULSEBUSSCHEDULE.TIMELINE]]
        port = dictionary[PULSEBUSSCHEDULE.PORT]
        return PulseBusSchedule(timeline=timeline, port=port)
