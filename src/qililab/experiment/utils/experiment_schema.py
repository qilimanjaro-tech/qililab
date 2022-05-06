"""SchemaDict class."""
from dataclasses import dataclass
from typing import List

from qililab.pulse.pulse import Pulse
from qililab.utils import nested_dataclass


@nested_dataclass
class ExperimentSchema:
    """ExecutionSchema class. Casts the execution dictionary into a class.
    The input to the constructor should be a dictionary with the following structure:

    - execution: settings dictionary.
    - pulse_sequence: list of pulse settings dictionaries.
    """

    settings: dict
    pulses: List[Pulse]

    def __post_init__(self):
        """Cast each pulse settings into a Pulse class."""
        self.pulses = [Pulse(settings=pulse) for pulse in self.pulses]
