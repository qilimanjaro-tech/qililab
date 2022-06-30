"""Platform class."""
from dataclasses import asdict
from typing import List

from qililab.constants import RUNCARD
from qililab.platform.components.bus_element import dict_factory
from qililab.platform.components.schema import Schema
from qililab.platform.utils import RuncardSchema
from qililab.settings import DDBBElement, TranslationSettings
from qililab.typings import BusSubcategory, Category, Parameter, yaml
from qililab.utils import nested_dataclass


class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        settings (PlatformSettings): Settings of the platform.
        schema (Schema): Schema object.
        buses (Buses): Container of Bus objects.
    """

    @nested_dataclass
    class PlatformSettings(DDBBElement):
        """Contains the settings of the platform.

        Args:
            number_qubits (int): Number of qubits used in the platform.
            drag_coefficient (float): Coefficient used for the drag pulse.
            num_sigmas (float): Number of sigmas that the pulse contains. sigma = pulse_duration / num_sigmas.
        """

        name: str
        translation_settings: TranslationSettings

    settings: PlatformSettings
    schema: Schema

    def __init__(self, runcard_schema: RuncardSchema):
        self.settings = self.PlatformSettings(**runcard_schema.settings)
        self.schema = Schema(**asdict(runcard_schema.schema))

    def connect(self):
        """Connect to the instruments."""
        self.instruments.connect()

    def close(self):
        """Close connection to the instruments."""
        self.instruments.close()

    def get_element(self, alias: str | None = None, category: Category | None = None, id_: int | None = None):
        """Get platform element.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            Tuple[object, list | None]: Element class together with the index of the bus where the element is located.
        """
        element = self.instruments.get_instrument(alias=alias, category=category, id_=id_)
        if element is None:
            element = (
                self.chip.get_node_from_id(node_id=id_) if alias is None else self.chip.get_node_from_alias(alias=alias)
            )
        if element is None:
            raise ValueError(f"Could not find element with alias {alias}, category {category} and id {id_}.")
        return element

    def get_bus(self, port: int, bus_subcategory: BusSubcategory):
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
                if bus.port == port and bus.subcategory == bus_subcategory
            ),
            ([], None),
        )

    def set_parameter(
        self,
        parameter: Parameter,
        value: float,
        alias: str | None = None,
        category: Category | None = None,
        id_: int | None = None,
    ):
        """Set parameter of a platform element.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
            value (float): New value.
        """
        if (alias is not None and alias == Category.PLATFORM.value) or (
            category is not None and Category(category) == Category.PLATFORM
        ):
            attr_type = type(getattr(self.settings.translation_settings, parameter.value))
            setattr(self.settings.translation_settings, parameter.value, attr_type(value))
            return
        element = self.get_element(alias=alias, category=category, id_=id_)
        element.set_parameter(parameter=parameter, value=value)

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
    def translation_settings(self):
        """Platform 'translation_settings' property.

        Returns:
            str: settings.translation_settings.
        """
        return self.settings.translation_settings

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
        return 1  # TODO: Compute num_qubits with Chip class.

    @property
    def instruments(self):
        """Platform 'instruments' property.

        Returns:
            Instruments: List of all instruments.
        """
        return self.schema.instruments

    @property
    def chip(self):
        """Platform 'chip' property.

        Returns:
            Chip: Class descibing the chip properties.
        """
        return self.schema.chip

    def to_dict(self):
        """Return all platform information as a dictionary."""
        platform_dict = {RUNCARD.SETTINGS: asdict(self.settings, dict_factory=dict_factory)}
        schema_dict = {RUNCARD.SCHEMA: self.schema.to_dict()}
        return platform_dict | schema_dict

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return str(yaml.dump(self.to_dict(), sort_keys=False))
