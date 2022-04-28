import json
from dataclasses import asdict, dataclass

from qililab.instruments import QubitInstrument
from qililab.platform.components.buses import Buses
from qililab.platform.components.schema import Schema
from qililab.platform.utils import dict_factory
from qililab.settings import GenericQubitInstrumentSettings
from qililab.typings import Category


class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        settings (PlatformSettings): Settings of the platform.
        schema (Schema): Schema object.
        buses (Buses): Container of Bus objects.
    """

    @dataclass
    class PlatformSettings(GenericQubitInstrumentSettings):
        """Contains the settings of the platform.

        Args:
            number_qubits (int): Number of qubits used in the platform.
            drag_coefficient (float): Coefficient used for the drag pulse.
            number_of_sigmas (float): Number of sigmas that the pulse contains. sigma = pulse_duration / number_of_sigmas.
        """

        number_qubits: int
        drag_coefficient: float
        number_of_sigmas: float

    def __init__(self, settings: dict, schema: Schema, buses: Buses):
        self.settings = self.PlatformSettings(**settings)
        self.schema = schema
        self.buses = buses

    def get_element(self, category: Category, id_: int):
        """Get platform element.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            object: Element class.
        """
        if category == Category.SCHEMA:
            return self.schema
        if category == Category.BUSES:
            return self.buses
        return self.schema.get_element(category=category, id_=id_)

    def connect(self):
        """Connect to the instruments."""
        self.buses.connect()

    def setup(self):
        """Setup instruments with platform settings."""
        QubitInstrument.general_setup(settings=self.settings)
        self.buses.setup()

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
        platform_dict = {Category.PLATFORM.value: asdict(self.settings, dict_factory=dict_factory)}
        schema_dict = {Category.SCHEMA.value: self.schema.to_dict()}
        return platform_dict | schema_dict

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return json.dumps(self.to_dict(), indent=4)
