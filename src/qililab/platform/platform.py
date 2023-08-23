"""Platform class."""
import ast
import re
from copy import deepcopy
from dataclasses import asdict
import warnings
from queue import Queue

from qibo.models import Circuit
from qiboconnection.api import API

from qililab.chip import Chip
from qililab.config import logger
from qililab.constants import GATE_ALIAS_REGEX, RUNCARD
from qililab.drivers import BaseInstrument,InstrumentDriverFactory
from qililab.drivers import Instruments as NewInstruments
from qililab.instrument_controllers import InstrumentController, InstrumentControllers
from qililab.instrument_controllers.utils import InstrumentControllerFactory
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseSchedule
from qililab.result import Result
from qililab.settings import Runcard
from qililab.system_control import ReadoutSystemControl
from qililab.typings.enums import Line, Parameter
from qililab.typings.yaml_type import yaml

from .components import Bus, Buses
from .components.bus_element import dict_factory


class Platform:  # pylint: disable = too-many-public-methods, too-many-instance-attributes
    """Platform object that describes setup used to control quantum devices.

    The class will receive the Runcard class, with all the inner GatesSettings, Chip, Bus classes that the Runcard class has created
    from the dictionaries, together with the instrument dictionaries that the Runcard class has not transform into classes yet.

    And with all that information instantiates the actual qililab Chip, Buses/Bus and corresponding Instrument classes.

    This class also handles the corresponding dis/connections, set_ups, set_parameters and turning the instruments on/off.

    Args:
        runcard (Runcard): Runcard class containing all the chip, buses & instruments information of the platform.
        connection (API | None = None): Qiboconnection's API class used to block access to other users when connected
            to the platform.

    Examples:

        .. note::

            The following examples contain made up results. These will soon be updated with real results.


        Imagine we want to run a Rabi sequence. To do so, we can first define a Qibo Circuit that contains a
        pi pulse and a measurement gate:

        .. code-block:: python3

            from qibo.models import Circuit
            from qibo import gates

            circuit = Circuit(1)
            circuit.add(gates.X(0))
            circuit.add(gates.M(0))

        For testing purposes, we can already execute this circuit using the platform. In order to execute a circuit or
        a pulse schedule we first need to connect to the platform:

        >>> platform.connect()
        >>> result = platform.execute(program=circuit, num_avg=1000, repetition_duration=6000)
        >>> result.array
        array([[5.],
                [5.]])

        When disabling scope acquisition mode, the array obtained has shape `(#sequencers, 2, #bins)`. In this case,
        given that we are using only 1 sequencer to acquire the results, we obtain an array with shape `(2, #bins)`.

        .. note::

            Remember that the values obtained correspond to the integral of the I/Q signals received by the
            digitiser.

        Now let's run the Rabi sequence. We will run this sequence by looping over the gain of the AWG used to
        create the pi pulse. To do so, we will use the `set_parameter` method with the alias of the bus used to
        drive qubit 0.

        .. code-block:: python3

            import numpy as np

            results = []

            gain_values = np.arange(0, 1, step=0.1)
            for gain in gain_values:
                # We assume the bus used to drive qubit 0 is called "drive_q0"
                platform.set_parameter(alias="drive_q0", parameter=ql.Parameter.GAIN, value=gain)
                result = platform.execute(program=circuit, num_avg=1000, repetition_duration=6000)
                results.append(result.array)

        No we can use `np.hstack` to stack the obtained results horizontally. By doing this, we will obtain an
        array with shape `(2, N)`, where N is the number of elements inside the loop:

        >>> results = np.hstack(results)
        >>> results
        array([[5, 4, 3, 2, 1, 2, 3],
                [5, 4, 3, 2, 1, 2, 3]])

        We can see how the integrated I/Q values oscillated, meaning that qubit 0 oscillates between ground and
        excited state!

        Given that we are looping over variables that are independent of the circuit (in this case the gain of the AWG),
        we can speed up the experiment by translating the circuit into pulses only once, and then executing the obtained
        pulses inside the loop:

        .. code-block:: python3

            from qililab.pulses.circuit_to_pulses import CircuitToPulses

            pulse_schedule = CircuitToPulses(platform=platform).translate(circuits=[circuit])

            results = []

            gain_values = np.arange(0, 1, step=0.1)
            for gain in gain_values:
                # We assume the bus used to drive qubit 0 is called "drive_q0"
                platform.set_parameter(alias="drive_q0", parameter=ql.Parameter.GAIN, value=gain)
                result = platform.execute(program=pulse_schedule, num_avg=1000, repetition_duration=6000)
                results.append(result.array)

        If we stack and print the results, we see how we obtain similar results, but much faster!

        >>> results = np.hstack(results)
        >>> results
        array([[5, 4, 3, 2, 1, 2, 3],
                [5, 4, 3, 2, 1, 2, 3]])
    """

    def __init__(self, runcard: Runcard, connection: API | None = None, new_drivers: bool = False):
        self.name = runcard.name
        """Name of the platform (str) """

        self.device_id = runcard.device_id
        """Device id of the platform (int). This attribute is needed for `qiboconnection` to save results remotely."""

        self.gates_settings = runcard.gates_settings
        """Dataclass with all the settings and gates definitions needed to decompose gates into pulses."""

        self.chip = Chip(**asdict(runcard.chip))
        """Chip class, instantiated given the ChipSettings class of the Runcard class"""

        if new_drivers:
            self.new_drivers = new_drivers
            # uses the new drivers and buses
            self.instruments: Instruments | NewInstruments = NewInstruments(elements=self._load_new_instruments(instruments_dict=runcard.instruments))
            """Instruments corresponding classes, instantiated given the instruments list[dict] of the Runcard class"""

            self.buses = None
            # TODO: uncomment this when from_dict is available
            # self.new_buses = Buses(
            #     elements=[
            #         BusDriver.from_dict(settings=asdict(bus), platform_instruments=self.new_instruments)
            #         for bus in runcard.buses
            #     ]
            # )
            """New Buses class, instantiated given the list[BusSettings] classes of the Runcard class"""
            self._connected_to_instruments: bool = True
            """Boolean describing the connection to the instruments. Defaults to False (not connected)."""
        else:
            self.instruments = Instruments(elements=self._load_instruments(instruments_dict=runcard.instruments))
            """Instruments corresponding classes, instantiated given the instruments list[dict] of the Runcard class"""

            self.instrument_controllers = InstrumentControllers(
                elements=self._load_instrument_controllers(instrument_controllers_dict=runcard.instrument_controllers)
            )
            """All the instrument controllers of the platform and their needed settings, contained as elements (`list[InstrumentController]`) inside an `InstrumentControllers` class."""

            self.buses = Buses(
                elements=[
                    Bus(settings=asdict(bus), platform_instruments=self.instruments, chip=self.chip)
                    for bus in runcard.buses
                ]
            )
            """All the buses of the platform and their needed settings, contained as elements (`list[Bus]`) inside a `Buses` class"""
            
            self._connected_to_instruments: bool = False
            """Boolean describing the connection to the instruments. Defaults to False (not connected)."""

        self.connection = connection
        """API connection of the platform. Same as the passed argument. Defaults to None."""


    def connect(self, manual_override=False):
        """Blocks the given device and connects to the instruments.

        Args:
            connection (API): qiboconnection's ``API`` class
            device_id (int): id of the device
            manual_override (bool, optional): If ``True``, avoid checking if the device is blocked. This will stop any
                current execution. Defaults to False.
        """
        if not self.new_drivers:
            if self._connected_to_instruments:
                logger.info("Already connected to the instruments")
                return

            if self.connection is not None and not manual_override:
                self.connection.block_device_id(device_id=self.device_id)

            self.instrument_controllers.connect()
            self._connected_to_instruments = True
            logger.info("Connected to the instruments")
        else:
            warnings.warn("This method is deprecated when using the new_drivers flag", DeprecationWarning)

    def initial_setup(self):
        """Set the initial setup of the instruments"""
        if not self.new_drivers:
            self.instrument_controllers.initial_setup()
            logger.info("Initial setup applied to the instruments")
        else:
            warnings.warn("This method is deprecated when using the new_drivers flag", DeprecationWarning)

    def turn_on_instruments(self):
        """Turn on the instruments"""
        if not self.new_drivers:
            self.instrument_controllers.turn_on_instruments()
            logger.info("Instruments turned on")
        else:
            warnings.warn("This method is deprecated when using the new_drivers flag", DeprecationWarning)

    def turn_off_instruments(self):
        """Turn off the instruments"""
        if not self.new_drivers:
            self.instrument_controllers.turn_off_instruments()
            logger.info("Instruments turned off")
        else:
            warnings.warn("This method is deprecated when using the new_drivers flag", DeprecationWarning)

    def disconnect(self):
        """Close connection to the instrument controllers."""
        if not self.new_drivers:
            if self.connection is not None:
                self.connection.release_device(device_id=self.device_id)
            if not self._connected_to_instruments:
                logger.info("Already disconnected from the instruments")
                return
            self.instrument_controllers.disconnect()
            self._connected_to_instruments = False
            logger.info("Disconnected from instruments")
        else:
            warnings.warn("This method is deprecated when using the new_drivers flag", DeprecationWarning)

    def get_element(self, alias: str):
        """Get platform element.

        Args:
            alias (str): Element alias to identify it.

        Returns:
            tuple[object, list | None]: Element class together with the index of the bus where the element is located.
        """
        if alias is not None:
            if alias == "platform":
                return self.gates_settings
            regex_match = re.search(GATE_ALIAS_REGEX, alias.split("_")[0])
            if regex_match is not None:
                name = regex_match["gate"]
                qubits_str = regex_match["qubits"]
                qubits = ast.literal_eval(qubits_str)
                if f"{name}({qubits_str})" in self.gates_settings.gate_names:
                    return self.gates_settings.get_gate(name=name, qubits=qubits)

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
        """Get bus given an alias."""
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
            parameter (Parameter): Name of the parameter to change.
            value (float | str | bool): New value to set.
            alias (str): Alias of the bus where the parameter is set.
            channel_id (int, optional): ID of the channel we want to use to set the parameter. Defaults to None.
        """
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        if alias == "platform" or regex_match is not None:
            self.gates_settings.set_parameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id)
            return
        element = self.get_element(alias=alias)
        element.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def _load_new_instruments(self, instruments_dict: list[dict]) -> list[BaseInstrument]:
        """Instantiate all instrument classes from their respective dictionaries and also set the inital parameters up.

        Args:
            instruments_dict (list[dict]): List of dictionaries containing the settings of each instrument.

        Returns:
            list[BaseInstrument]: List of instantiated instrument classes.
        """
        instruments = []
        for instrument in instruments_dict:
            local_dict = deepcopy(instrument)
            init_dict = {
                'alias': local_dict['alias'],
                'address': local_dict['address'],
            }
            instrument_instance = InstrumentDriverFactory.get(local_dict.pop(RUNCARD.TYPE))(**init_dict)
            instrument_instance.initial_setup(local_dict)
            instruments.append(instrument_instance)
        return instruments

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

    def to_dict(self):
        """Return all platform information as a dictionary."""
        name_dict = {RUNCARD.NAME: self.name}
        device_id = {RUNCARD.DEVICE_ID: self.device_id}
        gates_settings_dict = {RUNCARD.GATES_SETTINGS: asdict(self.gates_settings, dict_factory=dict_factory)}
        chip_dict = {RUNCARD.CHIP: self.chip.to_dict() if self.chip is not None else None}
        buses_dict = {RUNCARD.BUSES: self.buses.to_dict() if self.buses is not None else None}
        instrument_dict = {RUNCARD.INSTRUMENTS: self.instruments.to_dict() if self.instruments is not None else None}
        instrument_controllers_dict = {
            RUNCARD.INSTRUMENT_CONTROLLERS: self.instrument_controllers.to_dict()
            if self.instrument_controllers is not None
            else None,
        }

        return (
            name_dict
            | device_id
            | gates_settings_dict
            | chip_dict
            | buses_dict
            | instrument_dict
            | instrument_controllers_dict
        )

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
        num_bins: int = 1,
        queue: Queue | None = None,
    ) -> Result:
        """Execute a circuit or a pulse schedule using the platform instruments.

        If a Circuit is given, then it will be translated into a pulse schedule by using the transpilation
        settings of the platform.

        Args:
            program (PulseSchedule | Circuit): Circuit or pulse schedule to execute.
            num_avg (int): Number of hardware averages used.
            repetition_duration (int): Minimum duration of a single execution.
            num_bins (int, optional): Number of bins used. Defaults to 1.
            queue (Queue, optional): External queue used for asynchronous data handling. Defaults to None.

        Returns:
            Result: Result obtained from the execution. This corresponds to a numpy array that depending on the
                platform configuration may contain the following:

                - Scope acquisition is enabled: An array with dimension `(2, N)` which contain the scope data for
                    path0 (I) and path1 (Q). N corresponds to the length of the scope measured.

                - Scope acquisition disabled: An array with dimension `(#sequencers, 2, #bins)`.
        """
        # Compile pulse schedule
        programs = self.compile(program, num_avg, repetition_duration, num_bins)

        # Upload pulse schedule
        for bus_alias in programs:
            bus = self.get_bus_by_alias(alias=bus_alias)
            bus.upload()

        # Execute pulse schedule
        for bus_alias in programs:
            bus = self.get_bus_by_alias(alias=bus_alias)
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
