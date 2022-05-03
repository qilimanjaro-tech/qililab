"""PlatformDict class."""
from dataclasses import dataclass
from typing import List, Optional

from qililab.constants import YAML
from qililab.platform.utils.bus_element_hash_table import BusElementHashTable
from qililab.utils import nested_dataclass


@nested_dataclass
class PlatformDict:
    """PlatformDict class. Casts the platform dictionary into a class.
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
    class SchemaDict:
        """SchemaDict class."""

        @nested_dataclass
        class BusesDict:
            """BusesDict class."""

            @dataclass
            class BusDict:
                """BusDict class."""

                readout: bool
                qubit_instrument: dict
                signal_generator: dict
                mixer_up: dict
                qubit: Optional[dict] = None
                resonator: Optional[dict] = None
                mixer_down: Optional[dict] = None

                def __post_init__(self):
                    for name, value in self.__dict__.items():
                        if isinstance(value, dict):
                            elem_obj = BusElementHashTable.get(value[YAML.NAME])(value)
                            setattr(self, name, elem_obj)

            elements: List[BusDict]

            def __post_init__(self):
                self.elements = [self.BusDict(**element) for element in self.elements]

        buses: BusesDict

    schema: SchemaDict
    platform: dict
