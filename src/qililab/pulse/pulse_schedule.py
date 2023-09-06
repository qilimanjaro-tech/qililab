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
    """Class containing a list of PulseSequence objects. It is the pulsed representation of a Qibo circuit.

    Args:
        elements (list[PulseSequences]): List of pulse sequences.
    """

    elements: list[PulseBusSchedule] = field(default_factory=list)

    def add_event(self, pulse_event: PulseEvent, port: str, port_delay: int):
        """Add pulse event.

        Args:
            pulse_event (PulseEvent): PulseEvent object.
            port (str): Alias of the port of the chip targeted by the pulse event.
            port_delay (int): Delay (in ns) of the pulse event. This delay is added at the beginning of the pulse event.
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
        """Return dictionary representation of the class.

        Returns:
            dict: Dictionary representation of the class.
        """
        return {PULSESCHEDULES.ELEMENTS: [pulse_sequence.to_dict() for pulse_sequence in self.elements]}

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Build PulseSequence instance from dictionary.

        Args:
            dictionary (dict): Dictionary description of the class.

        Returns:
            PulseSequence: Class instance.
        """
        elements = [PulseBusSchedule.from_dict(dictionary=settings) for settings in dictionary[PULSESCHEDULES.ELEMENTS]]

        return PulseSchedule(elements=elements)

    def __iter__(self):
        """Redirect __iter__ magic method to elements."""
        return self.elements.__iter__()

    def __len__(self):
        """Redirect __len__ magic method to elements."""
        return len(self.elements)
