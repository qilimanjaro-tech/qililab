"""Platform class."""
from dataclasses import asdict

from qiboconnection.api import API

from qililab.config import logger
from qililab.constants import RUNCARD
from qililab.platform.components.bus_element import dict_factory
from qililab.platform.components.schema import Schema
from qililab.remote_connection.remote_api import RemoteAPI
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
        self._remote_api: RemoteAPI | None = None
        self._connected_to_instruments: bool = False
        self._initial_setup_applied: bool = False
        self._instruments_turned_on: bool = False

    def connect_and_set_initial_setup(
        self,
        automatic_turn_on_instruments: bool = False,
        connection: API | None = None,
        device_id: int | None = None,
        manual_override: bool = False,
    ):
        """Connect and set initial setup of the instruments

        Args:
            automatic_turn_on_instruments (bool, optional): Turn on the instruments. Defaults to False.
        """
        self.connect(connection=connection, device_id=device_id, manual_override=manual_override)
        if automatic_turn_on_instruments:
            self.turn_on_instruments()
        self.set_initial_setup()

    def connect(
        self,
        connection: API | None = None,
        device_id: int | None = None,
        manual_override: bool = False,
    ):
        """Connect to the instrument controllers."""
        if self._connected_to_instruments:
            logger.info("Already connected to the instruments")
            return

        self._remote_api = RemoteAPI(
            connection=connection,
            device_id=device_id,
            manual_override=manual_override,
        )
        self._remote_api.block_remote_device()
        self.instrument_controllers.connect()
        self._connected_to_instruments = True
        logger.info("Connected to the instruments")

    def set_initial_setup(self):
        """Set the initial setup of the instruments"""
        if self._initial_setup_applied:
            logger.info("Initial setup already applied to the instruments")
            return
        self.instrument_controllers.initial_setup()
        self._initial_setup_applied = True
        logger.info("Initial setup applied to the instruments")

    def turn_on_instruments(self):
        """Turn on the instruments"""
        if self._instruments_turned_on:
            logger.info("Instruments already turned on")
            return
        self.instrument_controllers.turn_on_instruments()
        self._instruments_turned_on = True
        logger.info("Instruments turned on")

    def turn_off_instruments(self):
        """Turn off the instruments"""
        if not self._instruments_turned_on:
            logger.info("Instruments already turned off")
            return
        self.instrument_controllers.turn_off_instruments()
        self._instruments_turned_on = False
        logger.info("Instruments turned off")

    def disconnect(self, automatic_turn_off_instruments: bool = False):
        """Close connection to the instrument controllers."""
        if not self._connected_to_instruments:
            logger.info("Already disconnected from the instruments")
            return
        if automatic_turn_off_instruments:
            self.turn_off_instruments()
        self.instrument_controllers.disconnect()
        if self._remote_api is not None:
            self._remote_api.release_remote_device()
        self._connected_to_instruments = False
        logger.info("Disconnected from instruments")

    def get_element(self, alias: str):
        """Get platform element.

        Args:
            alias (str): Element alias to identify it.

        Returns:
            Tuple[object, list | None]: Element class together with the index of the bus where the element is located.
        """
        if alias is not None and alias in ([Category.PLATFORM.value] + self.gate_names):
            return self.settings

        element = self.instruments.get_instrument(alias=alias)
        if element is None:
            element = self.instrument_controllers.get_instrument_controller(alias=alias)
        if element is None:
            element = self.get_bus_by_alias(alias=alias)
        if element is None:
            element = self.chip.get_node_from_alias(alias=alias)
        # if element is None:
        #     raise ValueError(f"Could not find element with alias {alias}.")
        return element

    def get_bus(self, port: int):
        """Find bus associated with the specified port.

        Args:
            port (int): port index of the chip

        Returns:
            Bus | None: Returns a Bus object or None if none is found.
        """
        return next(
            ((bus_idx, bus) for bus_idx, bus in enumerate(self.buses) if bus.port == port),
            ([], None),
        )

    def get_bus_by_alias(self, alias: str | None = None, category: Category | None = None, id_: int | None = None):
        """Get bus given an alias or id_ and category"""
        if alias is not None:
            return next(
                (element for element in self.buses if element.settings.alias == alias),
                None,
            )
        return next(
            (
                element
                for element in self.buses
                if element.id_ == id_ and element.settings.category == Category(category)
            ),
            None,
        )

    def set_parameter(
        self,
        parameter: Parameter,
        value: float | str | bool,
        alias: str,
        channel_id: int | None = None,
    ):
        """Set parameter of a platform element.

        Args:
            category (str): Category of the element.
            id_ (int): ID of the element.
            parameter (str): Name of the parameter to change.
            value (float): New value.
        """
        if alias in ([Category.PLATFORM.value] + self.gate_names):
            if alias == Category.PLATFORM.value:
                self.settings.set_parameter(parameter=parameter, value=value, channel_id=channel_id)
            else:
                self.settings.set_parameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id)
            return
        element = self.get_element(alias=alias)
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

    @property
    def remote_api(self):
        """Platform 'remote_api' property."""
        return self._remote_api

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
