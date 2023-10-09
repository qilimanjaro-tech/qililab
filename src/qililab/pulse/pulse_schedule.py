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

"""PulseSequence class."""
from dataclasses import dataclass, field

from qililab.constants import PULSESCHEDULES
from qililab.pulse.pulse_bus_schedule import PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent


@dataclass
class PulseSchedule:
    """Class containing a list of :class:`PulseBusSchedule` objects. It is the pulsed representation of a Qibo circuit.

    This class will receive a list of :class:`PulseBusSchedule` objects as argument. The class allows several operations to this
    list of PulseSequence objects and it is the class that allows to transpile pulse sequences into programs that run on quantum
    hardware control instruments.

    Args:
        elements (list[PulseBusSchedule]): List of :class:`PulseBusSchedule`.

    Examples:
        Imagine you want to create a PulseSchedule instance that will contain two :class:`PulseBusSchedule` objects, one for driving a qubit
        and the other one to do readout on the same qubit.

        To do so

        .. code-block:: python3

            drag_pulse = Pulse(
                amplitude=1,
                phase=0.5,
                duration=200,
                frequency=1e9,
                pulse_shape=Drag(num_sigmas=4, drag_coefficient=0.5)
            )
            readout_pulse = Pulse(
                amplitude=1,
                phase=0.5,
                duration=1500,
                frequency=1e9,
                pulse_shape=Rectangular())
            drag_pulse_event = PulseEvent(
                pulse=drag_pulse,
                start_time=0
            )
            readout_pulse_event = PulseEvent(
                pulse=readout_pulse,
                start_time=200,
                qubit=0
            )

            drive_schedule = PulseBusSchedule(
                timeline=[drag_pulse_event],
                port="drive_q0"
            )
            readout_schedule = PulseBusSchedule(
                timeline=[pulse_event],
                port="feedline_input"
            )
            list_pulse_bus_schedules = [drive_schedule, readout_schedule]

            pulse_schedule = PulseSchedule(list_pulse_bus_schedules)

        You can also create a pulse schedule by creating an instance of PulseSchedule class, with no pulse bus schedules passed
        as arguments, and dynamically adding pulses to the PulseSchedule class, which will then create a :class:`PulseBusSchedule` for
        each bus the pulses will be using.

        To do so, you can first create an instance of the PulseSchedule class, create each of the two pulses by creating two
        instances of the Pulse class, and then use the `add_event()` method of the PulseSchedule class to add the two pulses, wrapped
        by :class:`PulseEvent` class, to the schedule:

        .. code-block:: python3

            pulse_schedule = PulseSchedule()
            drag_pulse = Pulse(
                amplitude=1,
                phase=0.5,
                duration=200,
                frequency=1e9,
                pulse_shape=Drag(num_sigmas=4, drag_coefficient=0.5)
            )
            readout_pulse = Pulse(amplitude=1,
                                  phase=0.5,
                                  duration=1500,
                                  frequency=1e9,
                                  pulse_shape=Rectangular()
            )
            pulse_schedule.add_event(
                PulseEvent(pulse=drag_pulse, start_time=0),
                port="drive_q0",
                port_delay=0
            )
            pulse_schedule.add_event(
                PulseEvent(pulse=readout_pulse,start_time=200, qubit=0),
                port="feedline_input",
                port_delay=0
            )

        It is possible to serialize a PulseSchedule object as a dictionary. To do so you can use the `to_dict()` method:

        .. code-block:: python3

            pulse_schedule = PulseSchedule()
            drag_pulse = Pulse(
                amplitude=1,
                phase=0.5,
                duration=200,
                frequency=1e9,
                pulse_shape=Drag(num_sigmas=4, drag_coefficient=0.5)
            )
            readout_pulse = Pulse(amplitude=1,
                                  phase=0.5,
                                  duration=1500,
                                  frequency=1e9,
                                  pulse_shape=Rectangular()
            )
            pulse_schedule.add_event(
                PulseEvent(pulse=drag_pulse, start_time=0),
                port="drive_q0",
                port_delay=0
            )
            pulse_schedule.add_event(
                PulseEvent(pulse=readout_pulse,start_time=200, qubit=0),
                port="feedline_input",
                port_delay=0
            )

            pulse_schedule_dict = pulse_schedule.to_dict()

        It is also possible to create a PulseSchedule object from a dictionary that contains the serialized description of the
        object. To do so you can use the `from_dict()` method:

        .. code-block:: python3

            pulse_schedule = PulseSchedule()
            drag_pulse = Pulse(
                amplitude=1,
                phase=0.5,
                duration=200,
                frequency=1e9,
                pulse_shape=Drag(num_sigmas=4, drag_coefficient=0.5)
            )
            readout_pulse = Pulse(amplitude=1,
                                  phase=0.5,
                                  duration=1500,
                                  frequency=1e9,
                                  pulse_shape=Rectangular()
            )
            pulse_schedule.add_event(
                PulseEvent(pulse=drag_pulse, start_time=0),
                port="drive_q0",
                port_delay=0
            )
            pulse_schedule.add_event(
                PulseEvent(pulse=readout_pulse,start_time=200, qubit=0),
                port="feedline_input",
                port_delay=0
            )

            pulse_schedule_dict = pulse_schedule.to_dict()

            pulse_schedule = PulseSchedule.from_dict(pulse_schedule_dict)
    """

    elements: list[PulseBusSchedule] = field(default_factory=list)  #: List of pulse bus schedules.

    def add_event(self, pulse_event: PulseEvent, port: str, port_delay: int):
        """Adds pulse event to the list of pulse bus schedules.

        This functions receives a :class:`PulseEvent` object, a port (targetting a bus) and a port delay parameter, and checks whether
        there is already a PulseBusSchedule for the given port, adding the pulse event to the :class:`PulseBusSchedule`. If there is not
        a :class:`PulseBusSchedule` for that port, it creates a new one passing the pulse event and port as parameters, and adds this
        new instance to the list of :class:`PulseBusSchedule`.

        Args:
            pulse_event (PulseEvent): :class:`PulseEvent` object.
            port (str): Alias of the port of the chip targeted by the pulse event.
            port_delay (int): Delay (in ns) of the pulse event. This delay is added at the beginning of the :class:`PulseEvent`.
        """
        pulse_event.start_time += port_delay
        for pulse_sequence in self.elements:
            if port == pulse_sequence.port:
                pulse_sequence.add_event(pulse_event=pulse_event)
                return
        self.elements.append(PulseBusSchedule(timeline=[pulse_event], port=port))

    def create_schedule(self, port: str):
        """Creates an empty `PulseBusSchedule` that targets the given port.

        If the schedule already exists, nothing is done.

        Args:
            port (int): Target port of the schedule to create.
        """
        ports = {schedule.port for schedule in self.elements}
        if port not in ports:
            self.elements.append(PulseBusSchedule(port=port))

    def to_dict(self):
        """Returns dictionary representation of the class.

        Returns:
            dict: Dictionary representation of the class.
        """
        return {PULSESCHEDULES.ELEMENTS: [pulse_sequence.to_dict() for pulse_sequence in self.elements]}

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Builds PulseSequence instance from dictionary.

        Args:
            dictionary (dict): Dictionary description of the class.

        Returns:
            PulseSequence: Class instance.
        """
        elements = [PulseBusSchedule.from_dict(dictionary=settings) for settings in dictionary[PULSESCHEDULES.ELEMENTS]]

        return PulseSchedule(elements=elements)

    def __iter__(self):
        """Redirects __iter__ magic method to elements."""
        return self.elements.__iter__()

    def __len__(self):
        """Redirects __len__ magic method to elements."""
        return len(self.elements)
