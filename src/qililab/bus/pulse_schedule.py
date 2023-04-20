"""PulseSequence class."""
from dataclasses import dataclass, field
from typing import List

from qililab.bus.pulse_bus_schedule import PulseBusSchedule
from qililab.bus.pulse_event import PulseEvent


@dataclass
class PulseSchedule:
    """Class containing a list of PulseSequence objects. It is the pulsed representation of a Qibo circuit.

    Args:
        elements (List[PulseSequences]): List of pulse sequences.
    """

    elements: List[PulseBusSchedule] = field(default_factory=list)

    def add_event(self, pulse_event: PulseEvent, port: int):
        """Add pulse event.

        Args:
            pulse (PulseEvent): PulseEvent object.
        """
        for pulse_sequence in self.elements:
            if port == pulse_sequence.port:
                pulse_sequence.add_event(pulse_event=pulse_event)
                return
        self.elements.append(PulseBusSchedule(timeline=[pulse_event], port=port))

    def print(self) -> None:
        for element in self.elements:
            print(f"Port {element.port}: ", end="")
            for event in element:
                print(f"{event.pulse.name:->10s}", end="")
            print()

    def __iter__(self):
        """Redirect __iter__ magic method to elements."""
        return self.elements.__iter__()

    def __len__(self):
        """Redirect __len__ magic method to elements."""
        return len(self.elements)
