"""Platform class."""
from dataclasses import asdict

from qililab.constants import RUNCARD
from qililab.platform.components.bus_element import dict_factory
from qililab.platform.components.schema import Schema
from qililab.settings import RuncardSchema
from qililab.typings.enums import Category, Parameter
from qililab.typings.yaml_type import yaml


class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        settings (PlatformSettings): Settings of the platform.
        schema (Schema): Schema object.
        buses (Buses): Container of Bus objects.
    """

    settings: RuncardSchema.PlatformSettings
    schema: Schema

    def __init__(self, runcard_schema: RuncardSchema):
        self.settings = runcard_schema.settings
        self.schema = Schema(**asdict(runcard_schema.schema))

    def connect(self):
        """Connect to the instrument controllers."""
        self.instrument_controllers.connect()

    def close(self):
        """Close connection to the instrument controllers."""
        self.instrument_controllers.close()

    def get_element(self, alias: str | None = None, category: Category | None = None, id_: int | None = None):
        """Get platform element.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            Tuple[object, list | None]: Element class together with the index of the bus where the element is located.
        """
        if (alias is not None and alias in ([Category.PLATFORM.value] + self.gate_names)) or (
            category is not None and Category(category) == Category.PLATFORM
        ):
            return self.settings

        element = self.instruments.get_instrument(alias=alias, category=category, id_=id_)
        if element is None:
            element = self.instrument_controllers.get_instrument_controller(alias=alias, category=category, id_=id_)
        if element is None:
            if category is not None and id_ is not None:
                element = self.chip.get_node_from_id(node_id=id_)
            if alias is not None:
                element = self.chip.get_node_from_alias(alias=alias)
        if element is None:
            raise ValueError(f"Could not find element with alias {alias}, category {category} and id {id_}.")
        return element

    def get_bus(self, port: int):
        """Find bus of type 'bus_subcategory' that contains the given qubits.

        Args:
            qubit_ids (List[int]): List of qubit IDs.

        Returns:
            Bus | None: Returns a Bus object or None if none is found.
        """
        return next(
            ((bus_idx, bus) for bus_idx, bus in enumerate(self.buses) if bus.port == port),
            ([], None),
        )

    def set_parameter(
        self,
        parameter: Parameter,
        value: float,
        alias: str | None = None,
        category: Category | None = None,
        id_: int | None = None,
        channel_id: int | None = None,
    ):
        """Set parameter of a platform element.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
            value (float): New value.
        """
        if (alias is not None and alias in ([Category.PLATFORM.value] + self.gate_names)) or (
            category is not None and Category(category) == Category.PLATFORM
        ):
            if alias == Category.PLATFORM.value:
                self.settings.set_parameter(parameter=parameter, value=value, channel_id=channel_id)
            else:
                self.settings.set_parameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id)
            return
        element = self.get_element(alias=alias, category=category, id_=id_)
        element.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

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
        return self.chip.num_qubits

    @property
    def gate_names(self):
        """Platform 'gate_names' property.

        Returns:
            List[str]: List of the names of all the defined gates.
        """
        return self.settings.gate_names

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

    @property
    def instrument_controllers(self):
        """Platform 'instrument_controllers' property.

        Returns:
            InstrumentControllers: List of all instrument controllers.
        """
        return self.schema.instrument_controllers

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
