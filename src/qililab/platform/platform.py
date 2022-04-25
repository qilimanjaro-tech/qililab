import json
from dataclasses import asdict, dataclass

from qililab.platform.components.buses import Buses
from qililab.platform.components.schema import Schema
from qililab.platform.utils.dict_factory import dict_factory
from qililab.settings.settings import Settings
from qililab.typings import Category


class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        settings (Settings): Settings of the platform.
        schema (Schema): Schema object.
        buses (Buses): Container of Bus objects.
    """

    @dataclass
    class PlatformSettings(Settings):
        """Contains the settings of the platform.

        Args:
            number_qubits (int): Number of qubits used in the platform.
            hardware_average (int): Hardware average. Number of shots used when executing a sequence.
            software_average (float): Software average.
            repetition_duration (int): Duration (ns) of the whole program.
            delay_between_pulses (int): Delay (ns) between two consecutive pulses.
            drag_coefficient (float): Coefficient used for the drag pulse.
            number_of_sigmas (float): Number of sigmas that the pulse contains. sigma = pulse_duration / number_of_sigmas.
        """

        number_qubits: int
        hardware_average: int
        software_average: int
        repetition_duration: int  # ns
        delay_between_pulses: int  # ns
        delay_before_readout: int  # ns
        drag_coefficient: float
        number_of_sigmas: float

    def __init__(self, settings: dict, schema: Schema, buses: Buses):
        self.settings = self.PlatformSettings(**settings)
        self.schema = schema
        self.buses = buses

    @property
    def id_(self):
        """Platform 'id_' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def name(self):
        """Platform 'name' property.

        Returns:
            str: settings.name."""
        return self.settings.name

    @property
    def category(self):
        """Platform 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    def to_dict(self):
        """Return all platform information as a dictionary."""
        if not hasattr(self, "schema") or not hasattr(self, "buses"):
            raise AttributeError("Platform is not loaded.")
        platform_dict = {Category.PLATFORM.value: asdict(self.settings, dict_factory=dict_factory)}
        schema_dict = {Category.SCHEMA.value: self.schema.to_dict()}
        return platform_dict | schema_dict

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return json.dumps(self.to_dict(), indent=4)
