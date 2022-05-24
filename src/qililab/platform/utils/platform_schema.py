"""PlatformSchema class."""
from typing import List, Optional

from qililab.utils import nested_dataclass


@nested_dataclass
class PlatformSchema:
    """PlatformSchema class. Casts the platform dictionary into a class.
    The input to the constructor should be a dictionary with the following structure:

    - platform: settings dictionary.
    - schema: schema dictionary:
        - buses: buses dictionary:
            - elements: list of bus dictionaries with the following structure:
                - name: "readout" or "control"
                - qubit_instrument: settings dictionary.
                - signal_generator: settings dictionary.
                - mixer_up: settings dictionary.
                - qubit / resonator: settings dictionary.
                - mixer_down (optional): settings dictionary.
    """

    @nested_dataclass
    class Schema:
        """SchemaDict class."""

        @nested_dataclass
        class Bus:
            """BusDict class."""

            id_: int
            category: str
            bus_type: str
            system_control: dict
            qubit: Optional[dict] = None
            resonator: Optional[dict] = None

        elements: List[Bus]

        def __post_init__(self):
            self.elements = [self.Bus(**bus) for bus in self.elements]

    settings: dict
    schema: Schema
