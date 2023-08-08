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
            pulse (PulseEvent): PulseEvent object.
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
