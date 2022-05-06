"""PlatformSchema class."""
from dataclasses import dataclass
from typing import List, Optional

from qililab.settings import Settings
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

        @nested_dataclass
        class Bus:
            """BusDict class."""

            @dataclass
            class MixerSchema(Settings):
                """MixerSchema class."""

                epsilon: float
                delta: float
                offset_i: float
                offset_q: float

                def __iter__(self):
                    """Iterate over Bus elements.

                    Yields:
                        Tuple[str, float]: MixerSchema attributes.
                    """
                    yield from self.__dict__.items()

            readout: bool
            qubit_instrument: dict
            signal_generator: dict
            mixer_up: MixerSchema
            qubit: Optional[dict] = None
            resonator: Optional[dict] = None
            mixer_down: Optional[MixerSchema] = None

        elements: List[Bus]

        def __post_init__(self):
            self.elements = [self.Bus(**bus) for bus in self.elements]

    settings: dict
    schema: Schema
