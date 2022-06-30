"""PlatformSchema class."""
from typing import List

from qililab.utils import nested_dataclass


@nested_dataclass
class RuncardSchema:
    """PlatformSchema class. Casts the platform dictionary into a class.
    The input to the constructor should be a dictionary with the following structure:

    - platform: settings dictionary.
    - schema: schema dictionary:
        - buses: buses dictionary:
            - elements: list of bus dictionaries with the following structure:
                - name: "readout" or "control"
                - awg: settings dictionary.
                - signal_generator: settings dictionary.
                - qubit / resonator: settings dictionary.
    """

    @nested_dataclass
    class Schema:
        """SchemaDict class."""

        @nested_dataclass
        class BusSchema:
            """Bus schema class."""

            id_: int
            category: str
            subcategory: str
            system_control: dict
            port: int
            attenuator: dict | None = None

        @nested_dataclass
        class ChipSchema:
            """Chip schema class."""

            id_: int
            category: str
            nodes: List[dict]

        chip: ChipSchema
        buses: List[BusSchema]
        instruments: List[dict]

        def __post_init__(self):
            self.buses = [self.BusSchema(**bus) for bus in self.buses]

    settings: dict
    schema: Schema
