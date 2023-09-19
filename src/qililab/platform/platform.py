# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
from qililab.typings.enums import Line, Parameter
from qililab.typings.yaml_type import yaml

from .components import Bus, Buses
from .components.bus_element import dict_factory


class Platform:  # pylint: disable = too-many-public-methods, too-many-instance-attributes
    """Platform object representing the laboratory setup used to control the quantum devices.

    The platform is responsible for managing the initializations, connections, setups, and executions of the laboratory, which mainly consists of:

    - :class:`.Chip`

    - Buses

    - Instruments

    .. note::

        This class should be instantiated with the :meth:`qililab.build_platform()` function, by passing a serialized platform (runcard) dictionary
        or a path to the location of the YAML file containing it.

        You can find more information about the runcard structure, in the documentation :ref:`Runcards <runcards>` section.

    When you have an initilized :class:`Platform`, the typical first three steps (which normally only need to be done at the start) are:

    >>> platform.connect() # Connects to all the instruments.
    >>> platform.initial_setup()  # Sets the values stored in the runcard.
    >>> platform.turn_on_instruments()  # Turns the signal outputs on.

    And then, for each experiment you want to run, you normally would repeat:

    >>> platform.set_parameter(...) # Sets parameters in instruments.
    >>> result = platform.execute(...) # Executes the platform.

    Args:
        runcard (Runcard): Runcard dataclass containing the serialized platform (chip, instruments, buses...), created during :meth:`qililab.build_platform()` given a dictionary.
        connection (API | None = None): `Qiboconnection's <https://pypi.org/project/qiboconnection>`_ API class used to block access to other users when connected
            to the platform.

    Examples:

        .. note::

            All the following examples are explained in detail in the :ref:`Platform <platform>` section of the documentation. But a few thing to keep in mind:

            - In order to connect you need to have access to the IP’s addresses provided in the serialized platform (runcard), and connection is necessary for the next steps of the examples.

            - You might want to skip the `platform.initial_setup()` and the `platform.turn_on_instruments()` if you think nothing has been modified since last time, but we recommend you to do it always.

            - `platform.turn_on_instruments()` does not actually turn the instruments of the laboratory on, it only opens and closes their signal output generation.

            - You can print `platform.chip` and `platform.buses` at any moment, to check the platform structure.

        1. Executing a circuit with Platform:

            To execute a circuit you first need to define your circuit, for example one with a pi pulse and a measurement gate in qubit q (``int``),
            and then you also need to build, connect, setup and execute the platform, which together look like:

            .. code-block:: python

                import qililab as ql

                from qibo.models import Circuit
                from qibo import gates

                # Defining the Rabi circuit:
                circuit = Circuit(q+1)
                circuit.add(gates.X(q))
                circuit.add(gates.M(q))

                # Building the platform:
                platform = ql.build_platform(runcard="runcards/galadriel.yml")

                # Connecting and setting up the platform:
                platform.connect()
                platform.initial_setup()
                platform.turn_on_instruments()

                # Executing the platform:
                result = platform.execute(program=circuit, num_avg=1000, repetition_duration=6000)

            The results would look something like this:

            >>> result.array
            array([[5.],
                    [5.]])

            .. note::

                The obtained vlaue correspond to the integral of the I/Q signals received by the digitizer.
                And they have shape `(#sequencers, 2, #bins)`, in this case we only have 1 sequencer and 1 bin.

        |

        2. Running a Rabi sequence with Platform:

            To do a Rabi sequence, you precisely need the previous circuit and again you also need to build, connect and setup the platform,
            but this time, instead than executing the circuit once, you loop changing the gain parameter of the AWG (generator of the pi pulse):

            .. code-block:: python

                # Looping over the AWG gain to execute the Rabi sequence:
                results = []
                gain_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 1.0]

                for gain in gain_values:
                    platform.set_parameter(alias="drive_q0", parameter=ql.Parameter.GAIN, value=gain)
                    result = platform.execute(program=circuit, num_avg=1000, repetition_duration=6000)
                    results.append(result.array)

            Now you can use `np.hstack` to stack the results horizontally. By doing this, you would obtain an
            array with shape `(2, N)`, where N is the number of elements inside the loop:

            >>> import numpy as np
            >>> np.hstack(results)
            array([[5, 4, 3, 2, 1, 2, 3],
                    [5, 4, 3, 2, 1, 2, 3]])

            You can see how the integrated I/Q values oscillated, indicating that qubit 0 oscillates between ground and
            excited state!

        |

        3. Running a Rabi sequence faster, circuit to pulses:

            Since you are looping over variables that are independent of the circuit (in this case, the gain of the AWG),
            you can speed up the experiment by translating the circuit into pulses only once, and then, executing the obtained
            pulses inside the loop.

            Which is the same as before, but passing the `pulse_schedule` instead than the `circuit`, to the `execute` method:

            .. code-block:: python

                from qililab.pulse.circuit_to_pulses import CircuitToPulses

                # Translating the circuit to pulses:
                pulse_schedule = CircuitToPulses(platform=platform).translate(circuits=[circuit])

                # Looping over the AWG gain to execute the Rabi sequence:
                results = []
                gain_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 1.0]

                for gain in gain_values:
                    platform.set_parameter(alias="drive_q0", parameter=ql.Parameter.GAIN, value=gain)
                    result = platform.execute(program=pulse_schedule, num_avg=1000, repetition_duration=6000)
                    results.append(result.array)

            If you now stack and print the results, you obtain similar results, but much faster!

            >>> np.hstack(results)
            array([[5, 4, 3, 2, 1, 2, 3],
                    [5, 4, 3, 2, 1, 2, 3]])

        |

        4. Running a Ramsey, looping a parameter inside a the circuit:

            To do a Ramsey, you also need to build, connect and setup the platform as before, but this time the circuit is different from the previous,
            and you also this time you need to loop over a parameter of the circuit, concretely over the time of a wait gate.

            To run the Ramsey, you need to loop over the `t` parameter of the first Align gate. To do so, since the parameter is inside the
            circuit you need to use Qibo own `circuit.set_parameters` method, putting the parameters you want to set in the order they appear
            in the circuit construction:

            .. code-block:: python

                # Defining the Ramsey circuit:
                circuit = Circuit(q + 1)
                circuit.add(gates.RX(q, theta=np.pi/2))
                circuit.add(gates.Align(q, t=0))
                circuit.add(gates.RX(q, theta=np.pi/2))
                circuit.add(gates.Align(q, t=0))
                circuit.add(gates.M(q))

                # Looping over the wait time t, to execute the Ramsey:
                results_list = []
                wait_times = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

                for wait in wait_times:
                    circuit.set_parameters([np.pi/2, wait, np.pi/2, 0])
                    result = platform.execute(program=circuit, num_avg=1000, repetition_duration=6000)
                    results_list.append(result.array)

            so we were always setting `np.pi/2` to the `theta` parameter of the first `RX` gate, then the looped wait time `t` in the first `Align` gate,
            then another `np.pi/2` to the second `RX`, and finally a `0` to the second `Align` gate.
    """

    def __init__(self, runcard: Runcard, connection: API | None = None):
        self.name = runcard.name
        """Name of the platform (``str``) """

        self.device_id = runcard.device_id
        """Device id of the platform (``int``). This attribute is needed for `qiboconnection` to save results remotely."""

        self.gates_settings = runcard.gates_settings
        """Gate settings and definitions of the platform (``dataclass``). Needed to decompose gates into pulses. """

        self.instruments = Instruments(elements=self._load_instruments(instruments_dict=runcard.instruments))
        """All the instruments of the platform and their needed settings (``dataclass``). Each individual instrument is contained in a list inside the dataclass."""

        self.instrument_controllers = InstrumentControllers(
            elements=self._load_instrument_controllers(instrument_controllers_dict=runcard.instrument_controllers)
        )
        """All the instrument controllers of the platform and their needed settings (``dataclass``). Each individual instrument controller is contained in a list inside the dataclass."""

        self.chip = Chip(**asdict(runcard.chip))
        """Chip and nodes settings of the platform (:class:`.Chip` dataclass). Each individual node is contained in a list inside :class:`.Chip`."""

        self.buses = Buses(
            elements=[
                Bus(settings=asdict(bus), platform_instruments=self.instruments, chip=self.chip)
                for bus in runcard.buses
            ]
        )
        """All the buses of the platform and their needed settings (``dataclass``). Each individual bus is contained in a list inside the dataclass."""

        self.connection = connection
        """API connection of the platform (``API | None``). Same as the passed argument. Defaults to None."""

        self._connected_to_instruments: bool = False
        """Boolean describing the connection to the instruments. Defaults to False (not connected)."""

    def connect(self, manual_override=False):
        """Block the given device and connect to the instruments via qiboconnection's `API` and the `device_id`.

        Args:
            manual_override (bool, optional): If ``True``, avoid checking if the device is blocked (surpasses any blocked connection). This will stop any
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
        """Set the initial setup of the instruments."""
        self.instrument_controllers.initial_setup()
        logger.info("Initial setup applied to the instruments")

    def turn_on_instruments(self):
        """Turn on the instruments."""
        self.instrument_controllers.turn_on_instruments()
        logger.info("Instruments turned on")

    def turn_off_instruments(self):
        """Turn off the instruments."""
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
        """Get platform element and to which bus is connected, through its alias.

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
            element = self._get_bus_by_alias(alias=alias)
        if element is None:
            element = self.chip.get_node_from_alias(alias=alias)
        return element

    def _get_bus_by_qubit_index(self, qubit_index: int) -> tuple[Bus, Bus, Bus]:
        """Find buses associated with the given qubit index.

        Args:
            qubit_index (int): Qubit index to get the buses from.

        Returns:
            tuple[:class:`Bus`, :class:`Bus`, :class:`Bus`]: Tuple of Bus objects containing the flux, control and readout buses of the given qubit.
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

    def _get_bus_by_alias(self, alias: str | None = None):
        """Get bus given its alias.

        Args:
            alias (str | None, optional): Bus alias to identify it. Defaults to None.

        Returns:
            :class:`Bus`: Bus corresponding to the given alias. If none is found `None` is returned.

        """
        return next((bus for bus in self.buses if bus.alias == alias), None)

    def set_parameter(
        self,
        parameter: Parameter,
        value: float | str | bool,
        alias: str,
        channel_id: int | None = None,
    ):
        """Set a parameter of a platform element.

        Args:
            parameter (Parameter): Name of the parameter to change.
            value (float | str | bool): New value to set in the parameter.
            alias (str): Alias of the bus where the parameter is set.
            channel_id (int, optional): ID of the channel we want to use to set the parameter. Defaults to None.
        """
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        if alias == "platform" or regex_match is not None:
            self.gates_settings.set_parameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id)
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

    def to_dict(self):
        """Return all platform information as a dictionary. Used for the platform serialization.

        Returns:
            dict: Dictionary of the serialized platform.
        """
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
        """String representation of the platform.

        Returns:
            str: Name of the platform.
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

        If a :class:`Circuit` is given, then it will be translated into a :class:`PulseSchedule` by using the transpilation
        settings of the platform.

        Args:
            program (:class:`PulseSchedule` | :class:`Circuit`): Circuit or pulse schedule to execute.
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
            bus = self._get_bus_by_alias(alias=bus_alias)
            bus.upload()

        # Execute pulse schedule
        for bus_alias in programs:
            bus = self._get_bus_by_alias(alias=bus_alias)
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
            program (:class:`PulseSchedule` | :class:`Circuit`): Circuit or pulse schedule to compile.
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
