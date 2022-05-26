"""Platform class."""
import json
from dataclasses import asdict
from typing import List

from qililab.platform.components.schema import Schema
from qililab.platform.utils import PlatformSchema, dict_factory
from qililab.settings import Settings
from qililab.typings import BusSubcategory, Category
from qililab.utils import nested_dataclass


class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        settings (PlatformSettings): Settings of the platform.
        schema (Schema): Schema object.
        buses (Buses): Container of Bus objects.
    """

    @nested_dataclass
    class PlatformSettings(Settings):
        """Contains the settings of the platform.

        Args:
            number_qubits (int): Number of qubits used in the platform.
            drag_coefficient (float): Coefficient used for the drag pulse.
            num_sigmas (float): Number of sigmas that the pulse contains. sigma = pulse_duration / num_sigmas.
        """

        name: str

    settings: PlatformSettings
    schema: Schema
    _schema: PlatformSchema

    def __init__(self, platform_schema: PlatformSchema):
        self.settings = self.PlatformSettings(**platform_schema.settings)
        self.schema = Schema(**asdict(platform_schema.schema, dict_factory=dict_factory))
        self._schema = platform_schema

    def get_element(self, category: Category, id_: int = 0):
        """Get platform element.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            Tuple[object, list | None]: Element class together with the index of the bus where the element is located.
        """
        if category == Category.SCHEMA:
            return self.schema, None
        if category == Category.BUSES:
            return self.buses, None
        return self.schema.get_element(category=category, id_=id_)

    def get_bus(self, qubit_ids: List[int], bus_subcategory: BusSubcategory):
        """Find bus of type 'bus_subcategory' that contains the given qubits.

        Args:
            qubit_ids (List[int]): List of qubit IDs.
            bus_subcategory (BusSubcategory): Type of bus. Options are "control" and "readout".

        Returns:
            Bus | None: Returns a Bus object or None if none is found.
        """
        return next(
            (
                (bus_idx, bus)
                for bus_idx, bus in enumerate(self.buses)
                if bus.qubit_ids == qubit_ids and bus.subcategory == bus_subcategory
            ),
            ([], None),
        )

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
            str: settings.name.
        """
        return self.settings.name

    @property
    def category(self):
        """Platform 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    @property
    def buses(self):
        """Platform 'buses' property.

        Returns:
            Buses: schema.buses.
        """
        return self.schema.buses

    @property
    def num_qubits(self):
        """Platform 'num_qubits' property.

        Returns:
            int: Number of different qubits that the platform contains.
        """
        qubit_sum = 0
        while self.get_element(category=Category.QUBIT, id_=qubit_sum)[0] is not None:
            qubit_sum += 1
        return qubit_sum

    def to_dict(self):
        """Return all platform information as a dictionary."""
        return asdict(self._schema, dict_factory=dict_factory)

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return json.dumps(self.to_dict(), indent=4)
