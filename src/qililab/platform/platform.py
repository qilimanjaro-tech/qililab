"""Platform class."""
import ast
import re
from copy import deepcopy
from dataclasses import asdict
from queue import Queue

from qibo.models import Circuit
from qiboconnection.api import API

from qililab.chip import Chip
from qililab.config import logger
from qililab.constants import GATE_ALIAS_REGEX, RUNCARD
from qililab.instrument_controllers import InstrumentController, InstrumentControllers
from qililab.instrument_controllers.utils import InstrumentControllerFactory
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseSchedule
from qililab.result import Result
from qililab.settings import Runcard
from qililab.system_control import ReadoutSystemControl
from qililab.typings.enums import Category, Line, Parameter
from qililab.typings.yaml_type import yaml

from .components import Bus, Buses
from .components.bus_element import dict_factory


class Platform:  # pylint: disable=too-many-public-methods
    """Platform object that describes setup used to control quantum devices.

    The class will receive the Runcard class, with all the GateSettings, ChipSettings, BusSettings that the
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

        self.gate_settings = runcard.gate_settings
        """Exactly the gate_settings in the Runcard class"""

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
                return self.gate_settings
            regex_match = re.search(GATE_ALIAS_REGEX, alias.split("_")[0])
            if regex_match is not None:
                name = regex_match["gate"]
                qubits_str = regex_match["qubits"]
                qubits = ast.literal_eval(qubits_str)
                if f"{name}({qubits_str})" in self.gate_settings.gate_names:
                    return self.gate_settings.get_gate(name=name, qubits=qubits)

        element = self.instruments.get_instrument(alias=alias)
        if element is None:
            element = self.instrument_controllers.get_instrument_controller(alias=alias)
        if element is None:
            element = self.get_bus_by_alias(alias=alias)
        if element is None:
            element = self.chip.get_node_from_alias(alias=alias)
        return element

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
        flux_bus = self.buses.get(port=flux_port)
        control_bus = self.buses.get(port=control_port)
        readout_bus = self.buses.get(port=readout_port)
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
            self.gate_settings.set_parameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id)
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
    def name(self):
        """Platform 'name' property.

        Returns:
            str: settings.name.
        """
        return self.gate_settings.name

    @property
    def device_id(self):
        """Returns the id of the platform device.

        Returns:
            int: id of the platform device
        """
        return self.gate_settings.device_id

    def to_dict(self):
        """Return all platform information as a dictionary."""
        gate_settings_dict = {RUNCARD.GATE_SETTINGS: asdict(self.gate_settings, dict_factory=dict_factory)}
        chip_dict = {RUNCARD.CHIP: self.chip.to_dict() if self.chip is not None else None}
        buses_dict = {RUNCARD.BUSES: self.buses.to_dict() if self.buses is not None else None}
        instrument_dict = {RUNCARD.INSTRUMENTS: self.instruments.to_dict() if self.instruments is not None else None}
        instrument_controllers_dict = {
            RUNCARD.INSTRUMENT_CONTROLLERS: self.instrument_controllers.to_dict()
            if self.instrument_controllers is not None
            else None,
        }

        return gate_settings_dict | chip_dict | buses_dict | instrument_dict | instrument_controllers_dict

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return str(yaml.dump(self.to_dict(), sort_keys=False))

    def execute(
        self,
        program: PulseSchedule | Circuit,
        num_avg: int,
        repetition_duration: int,
        num_bins: int,
        queue: Queue | None = None,
    ) -> Result:
        """Execute a circuit or a pulse schedule using the platform instruments.

        If a Circuit is given, then it will be translated into a pulse schedule by using the transpilation
        settings of the platform.

        Args:
            program (PulseSchedule | Circuit): Circuit or pulse schedule to execute.
            num_avg (int): Number of hardware averages used.
            repetition_duration (int): Minimum duration of a single execution.
            num_bins (int): Number of bins used.
            queue (Queue, optional): External queue used for asynchronous data handling. Defaults to None.

        Returns:
            Result: Result obtained from the execution. This corresponds to a numpy array that depending on the
                platform configuration may contain the following:

                - Scope acquisition is enabled: An array with dimension `(N, 2)` which contain the scope data for
                    path0 (I) and path1 (Q). N corresponds to the length of the scope measured.

                - Scope acquisition disabled: An array with dimension `(#sequencers, #bins, 2)
        """
        # Compile pulse schedule
        self.compile(program, num_avg, repetition_duration, num_bins)

        # Upload pulse schedule
        for bus in self.buses:
            bus.upload()

        # Execute pulse schedule
        for bus in self.buses:
            bus.run()

        # Acquire results
        readout_buses = [bus for bus in self.buses if isinstance(bus.system_control, ReadoutSystemControl)]
        results: list[Result] = []
        for bus in readout_buses:
            result = bus.acquire_result()
            if queue is not None:
                queue.put_nowait(item=result)
            results.append(result)

        # FIXME: set multiple readout buses
        if len(results) > 1:
            logger.error("Only One Readout Bus allowed. Reading only from the first one.")
        if not results:
            raise ValueError("There are no readout buses in the platform.")

        return results[0]

    def compile(self, program: PulseSchedule | Circuit, num_avg: int, repetition_duration: int, num_bins: int) -> dict:
        """Compiles the circuit / pulse schedule into a set of assembly programs.

        Args:
            program (PulseSchedule | Circuit): Circuit to compile.
            num_avg (int): Number of hardware averages used.
            repetition_duration (int): Minimum duration of a single execution.
            num_bins (int): Number of bins used.

        Returns:
            dict: Dictionary of compiled assembly programs.
        """
        # We have a circular import because Platform uses CircuitToPulses and vice versa
        from qililab.pulse.circuit_to_pulses import (  # pylint: disable=import-outside-toplevel, cyclic-import
            CircuitToPulses,
        )

        if isinstance(program, Circuit):
            translator = CircuitToPulses(platform=self)
            pulse_schedule = translator.translate(circuits=[program])[0]
        else:
            pulse_schedule = program

        programs = {}
        for pulse_bus_schedule in pulse_schedule.elements:
            bus = self.buses.get(port=pulse_bus_schedule.port)
            bus_programs = bus.compile(pulse_bus_schedule, num_avg, repetition_duration, num_bins)
            programs[bus.alias] = bus_programs

        return programs
