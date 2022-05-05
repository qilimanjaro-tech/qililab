"""PlatformSchema class."""
from dataclasses import dataclass
from typing import List, Optional

from qililab.utils import nested_dataclass


# TODO: I am currently not using this class. I leave it here if we need to use it later on.
@nested_dataclass
class PlatformSchema:
    """PlatformSchema class. Casts the platform dictionary into a class.
    The input to the constructor should be a dictionary with the following structure:

    - platform: settings dictionary.
    - schema: schema dictionary:
        - buses: buses dictionary:
            - elements: list of bus dictionaries with the following structure:
                - name: "readout" or "readout"
                - qubit_instrument: settings dictionary.
                - signal_generator: settings dictionary.
                - mixer_up: settings dictionary.
                - qubit / resonator: settings dictionary.
                - mixer_down (optional): settings dictionary.
    """

    @nested_dataclass
    class Schema:
        """SchemaDict class."""

        @dataclass
        class Bus:
            """BusDict class."""

            readout: bool
            qubit_instrument: dict
            signal_generator: dict
            mixer_up: dict
            qubit: Optional[dict] = None
            resonator: Optional[dict] = None
            mixer_down: Optional[dict] = None

        elements: List[Bus]

        def __post_init__(self):
            self.elements = [self.Bus(**bus) for bus in self.elements]

    settings: dict
    schema: Schema
