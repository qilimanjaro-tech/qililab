"""Platform class."""
import ast
import re
from copy import deepcopy
from dataclasses import asdict

from qiboconnection.api import API

from qililab.chip import Chip
from qililab.config import logger
from qililab.constants import GATE_ALIAS_REGEX, RUNCARD
from qililab.instrument_controllers import InstrumentController, InstrumentControllers
from qililab.instrument_controllers.utils import InstrumentControllerFactory
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.instruments.utils import InstrumentFactory
from qililab.platform.components import Bus, Buses
from qililab.platform.components.bus_element import dict_factory
from qililab.settings import Runcard
from qililab.typings.enums import Category, Line, Parameter
from qililab.typings.yaml_type import yaml


class Platform:  # pylint: disable=too-many-public-methods
    """Platform object that describes setup used to control quantum devices.

    The class will receive the Runcard class, with all the TranspilationSettings, ChipSettings, BusSettings that the
    Runcard class has created from the dictionaries, together with the instrument dictionaries that the Runcard class
    has not transform into classes yet.

    And with all that information instantiates the actual qililab Chip, Buses/Bus and corresponding Instrument classes.

    This class also handles the corresponding dis/connections, set_ups, set_parameters and turning the instruments on/off.

    Args:
        runcard (Runcard): Runcard class containing all the chip, buses & instruments information of the platform.
        connection (API | None = None): Connection of the platform.
    """

    def __init__(self, runcard: Runcard, connection: API | None = None):
        """instantiates the platform"""

        self.transpilation_settings = runcard.transpilation_settings
        """Exactly the transpilation_settings in the Runcard class"""

        self.instruments = Instruments(elements=self._load_instruments(instruments_dict=runcard.instruments))
        """Instruments corresponding classes, instantiated given the instruments list[dict] of the Runcard class"""

        self.instrument_controllers = InstrumentControllers(
            elements=self._load_instrument_controllers(instrument_controllers_dict=runcard.instrument_controllers)
        )
        """InstrumentControllers corresponding classes, instantiated given the instrument_controllers list[dict] of the Runcard class"""

        self.chip = Chip(**asdict(runcard.chip))
        """Chip class, instantiated given the ChipSettings class of the Runcard class"""

        self.buses = Buses(
            elements=[
                Bus(settings=asdict(bus), platform_instruments=self.instruments, chip=self.chip)
                for bus in runcard.buses
            ]
        )
        """Buses class, instantiated given the list[BusSettings] classes of the Runcard class"""

        self.connection = connection
        """Connection of the platform. Same as the argument"""

        self._connected_to_instruments: bool = False
        """Boolean describing the connection to instruments. Defaults to False (not connected)"""

    def connect(self, manual_override=False):
        """Blocks the given device and connects to the instruments.

        Args:
            connection (API): qiboconnection's ``API`` class
            device_id (int): id of the device
            manual_override (bool, optional): If ``True``, avoid checking if the device is blocked. This will stop any
                current execution. Defaults to False.
        """
        if self._connected_to_instruments:
            logger.info("Already connected to the instruments")
            return

        if self.connection is not None and not manual_override:
            self.connection.block_device_id(device_id=self.device_id)

        self.instrument_controllers.connect()
        self._connected_to_instruments = True
        logger.info("Connected to the instruments")

    def initial_setup(self):
        """Set the initial setup of the instruments"""
        self.instrument_controllers.initial_setup()
        logger.info("Initial setup applied to the instruments")

    def turn_on_instruments(self):
        """Turn on the instruments"""
        self.instrument_controllers.turn_on_instruments()
        logger.info("Instruments turned on")

    def turn_off_instruments(self):
        """Turn off the instruments"""
        self.instrument_controllers.turn_off_instruments()
        logger.info("Instruments turned off")

    def disconnect(self):
        """Close connection to the instrument controllers."""
        if self.connection is not None:
            self.connection.release_device(device_id=self.device_id)
        if not self._connected_to_instruments:
            logger.info("Already disconnected from the instruments")
            return
        self.instrument_controllers.disconnect()
        self._connected_to_instruments = False
        logger.info("Disconnected from instruments")

    def get_element(self, alias: str):
        """Get platform element.

        Args:
            alias (str): Element alias to identify it.

        Returns:
            tuple[object, list | None]: Element class together with the index of the bus where the element is located.
        """
        if alias is not None:
            if alias == Category.PLATFORM.value:
                return self.transpilation_settings
            regex_match = re.search(GATE_ALIAS_REGEX, alias)
            if regex_match is not None:
                name = regex_match["gate"]
                qubits_str = regex_match["qubits"]
                qubits = ast.literal_eval(qubits_str)
                if name in self.gate_names:
                    return self.transpilation_settings.get_gate(name=name, qubits=qubits)

        element = self.instruments.get_instrument(alias=alias)
        if element is None:
            element = self.instrument_controllers.get_instrument_controller(alias=alias)
        if element is None:
            element = self.get_bus_by_alias(alias=alias)
        if element is None:
            element = self.chip.get_node_from_alias(alias=alias)
        return element

    def get_bus(self, port: int) -> tuple[int, Bus] | tuple[list, None]:
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

    def get_bus_by_qubit_index(self, qubit_index: int) -> tuple[Bus, Bus, Bus]:
        """Find bus associated with the given qubit index.

        Args:
            qubit_index (int): qubit index

        Returns:
            tuple[Bus, Bus, Bus]: Returns a tuple of Bus objects containing the flux, control and readout buses of the given qubit
        """
        flux_port = self.chip.get_port_from_qubit_idx(idx=qubit_index, line=Line.FLUX)
        control_port = self.chip.get_port_from_qubit_idx(idx=qubit_index, line=Line.DRIVE)
        readout_port = self.chip.get_port_from_qubit_idx(idx=qubit_index, line=Line.FEEDLINE_INPUT)
        flux_bus = self.get_bus(port=flux_port)[1]
        control_bus = self.get_bus(port=control_port)[1]
        readout_bus = self.get_bus(port=readout_port)[1]
        if flux_bus is None or control_bus is None or readout_bus is None:
            raise ValueError(
                f"Could not find buses for qubit {qubit_index} connected to the ports "
                f"{flux_port}, {control_port} and {readout_port}."
            )
        return flux_bus, control_bus, readout_bus

    def get_bus_by_alias(self, alias: str | None = None):
        """Get bus given an alias or id_ and category"""
        return next((bus for bus in self.buses if bus.alias == alias), None)

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
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        if alias == Category.PLATFORM.value or regex_match is not None:
            self.transpilation_settings.set_parameter(
                alias=alias, parameter=parameter, value=value, channel_id=channel_id
            )
            return
        element = self.get_element(alias=alias)
        element.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def _load_instruments(self, instruments_dict: list[dict]) -> list[Instrument]:
        """Instantiate all instrument classes from their respective dictionaries.

        Args:
            instruments_dict (list[dict]): List of dictionaries containing the settings of each instrument.

        Returns:
            list[Instrument]: List of instantiated instrument classes.
        """
        instruments = []
        for instrument in instruments_dict:
            local_dict = deepcopy(instrument)
            instruments.append(InstrumentFactory.get(local_dict.pop(RUNCARD.NAME))(settings=local_dict))
        return instruments

    def _load_instrument_controllers(self, instrument_controllers_dict: list[dict]) -> list[InstrumentController]:
        """Instantiate all instrument controller classes from their respective dictionaries.

        Args:
            instrument_controllers_dict (list[dict]): List of dictionaries containing
            the settings of each instrument controller.

        Returns:
            list[InstrumentController]: List of instantiated instrument controller classes.
        """
        instrument_controllers = []
        for instrument_controller in instrument_controllers_dict:
            local_dict = deepcopy(instrument_controller)
            instrument_controllers.append(
                InstrumentControllerFactory.get(local_dict.pop(RUNCARD.NAME))(
                    settings=local_dict, loaded_instruments=self.instruments
                )
            )
        return instrument_controllers

    @property
    def id_(self):
        """Platform 'id_' property.

        Returns:
            int: settings.id_.
        """
        return self.transpilation_settings.id_

    @property
    def name(self):
        """Platform 'name' property.

        Returns:
            str: settings.name.
        """
        return self.transpilation_settings.name

    @property
    def category(self):
        """Platform 'category' property.

        Returns:
            str: settings.category.
        """
        return self.transpilation_settings.category

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
            list[str]: List of the names of all the defined gates.
        """
        return self.transpilation_settings.gate_names

    @property
    def device_id(self):
        """Returns the id of the platform device.

        Returns:
            int: id of the platform device
        """
        return self.transpilation_settings.device_id

    def to_dict(self):
        """Return all platform information as a dictionary."""
        settings_dict = {RUNCARD.TRANSPILATION_SETTINGS: asdict(self.transpilation_settings, dict_factory=dict_factory)}
        chip_dict = {RUNCARD.CHIP: self.chip.to_dict() if self.chip is not None else None}
        buses_dict = {RUNCARD.BUSES: self.buses.to_dict() if self.buses is not None else None}
        instrument_dict = {RUNCARD.INSTRUMENTS: self.instruments.to_dict() if self.instruments is not None else None}
        instrument_controllers_dict = {
            RUNCARD.INSTRUMENT_CONTROLLERS: self.instrument_controllers.to_dict()
            if self.instrument_controllers is not None
            else None,
        }

        return settings_dict | chip_dict | buses_dict | instrument_dict | instrument_controllers_dict

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return str(yaml.dump(self.to_dict(), sort_keys=False))
