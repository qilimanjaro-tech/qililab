"""Platform class."""
import ast
import re
from dataclasses import asdict

from qiboconnection.api import API

from qililab.config import logger
from qililab.constants import GATE_ALIAS_REGEX, RUNCARD
from qililab.platform.components import Bus, Schema
from qililab.platform.components.bus_element import dict_factory
from qililab.qprogram import QBloxCompiler, QProgram, Settings
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.settings import RuncardSchema
from qililab.typings.enums import Category, Line, Parameter
from qililab.typings.yaml_type import yaml


class Platform:  # pylint: disable=too-many-public-methods
    """Platform object that describes setup used to control quantum devices.

    Args:
        settings (PlatformSettings): Settings of the platform.
        schema (Schema): Schema object.
        buses (Buses): Container of Bus objects.
    """

    def __init__(self, runcard_schema: RuncardSchema, connection: API | None = None):
        self.settings = runcard_schema.settings
        self.schema = Schema(**asdict(runcard_schema.schema))  # type: ignore
        self.connection = connection
        self._connected_to_instruments: bool = False

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

    def execute_qprogram(self, qprogram: QProgram) -> list[QbloxResult]:
        """Compile and execute a qprogram on the buses of the platform.

        NOTE: this method might have issues when the platform is used with the old buses, because they don't
        have the 'execute_qpysequence' method (actually not even the 'execute' method). This should be handled
        somehow, to maintain backwards compatibility.

        Args:
            qprogram (QProgram): The qprogram to execute.

        Returns:
            A list where each element is the results of the acquisition performed by a readout bus.
            These results are represented as instances of the QbloxResult class.
        """
        compiler = QBloxCompiler(settings=Settings())
        compiled_results = compiler.compile(qprogram)

        for bus in self.buses:
            sequence = compiled_results[bus.alias]
            bus.execute_qpysequence(sequence)

        results = []
        for bus in self.buses.readout_buses():
            result = bus.acquire_results()
            results.append(result)

        return results

    def get_element(self, alias: str):
        """Get platform element.

        Args:
            alias (str): Element alias to identify it.

        Returns:
            tuple[object, list | None]: Element class together with the index of the bus where the element is located.
        """
        if alias is not None:
            if alias == Category.PLATFORM.value:
                return self.settings
            regex_match = re.search(GATE_ALIAS_REGEX, alias.split("_")[0])
            if regex_match is not None:
                name = regex_match["gate"]
                qubits_str = regex_match["qubits"]
                qubits = ast.literal_eval(qubits_str)
                if f"{name}({qubits_str})" in self.gate_names:
                    return self.settings.get_gate(name=name, qubits=qubits)

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
            list[str]: List of the names of all the defined gates.
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
    def device_id(self):
        """Returns the id of the platform device.

        Returns:
            int: id of the platform device
        """
        return self.settings.device_id

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
