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
import io
import re
from copy import deepcopy
from dataclasses import asdict
from queue import Queue

import numpy as np
from qibo.gates import M
from qibo.models import Circuit
from qiboconnection.api import API
from qm import generate_qua_script
from qpysequence import Sequence as QpySequence
from ruamel.yaml import YAML

from qililab.chip import Chip
from qililab.circuit_transpiler import CircuitTranspiler
from qililab.config import logger
from qililab.constants import GATE_ALIAS_REGEX, RUNCARD
from qililab.instrument_controllers import InstrumentController, InstrumentControllers
from qililab.instrument_controllers.utils import InstrumentControllerFactory
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.instruments.qblox import QbloxModule
from qililab.instruments.quantum_machines import QuantumMachinesCluster
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseSchedule
from qililab.pulse import QbloxCompiler as PulseQbloxCompiler
from qililab.qprogram import QbloxCompiler, QProgram, QuantumMachinesCompiler
from qililab.result import Result
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.result.qprogram.qprogram_results import QProgramResults
from qililab.result.qprogram.quantum_machines_measurement_result import QuantumMachinesMeasurementResult
from qililab.settings import Runcard
from qililab.system_control import ReadoutSystemControl
from qililab.typings.enums import InstrumentName, Line, Parameter
from qililab.utils import hash_qpy_sequence

from .components import Bus, Buses


class Platform:  # pylint: disable = too-many-public-methods, too-many-instance-attributes
    """Platform object representing the laboratory setup used to control quantum devices.

    The platform is responsible for managing the initializations, connections, setups, and executions of the laboratory, which mainly consists of:

    - :class:`.Chip`

    - Buses

    - Instruments

    .. note::

        This class should be instantiated with the :meth:`ql.build_platform()` function, either by passing a :ref:`runcard <runcards>` (serialized platform dictionary)
        or a path to the location of the YAML file containing it.

        More information about the runcard structure, in the :ref:`Runcards <runcards>` section of the documentation.

    After initializing a :class:`Platform`, the typical first three steps (which are usually only required at the start) are:

    >>> platform.connect() # Connects to all the instruments.
    >>> platform.initial_setup()  # Sets the parameters defined in the runcard.
    >>> platform.turn_on_instruments()  # Turns on the signal outputs.

    And then, for each experiment you want to run, you would typically repeat:

    >>> platform.set_parameter(...) # Sets any parameter of the Platform.
    >>> result = platform.execute(...) # Executes the platform.

    Args:
        runcard (Runcard): Dataclass containing the serialized platform (chip, instruments, buses...), created during :meth:`ql.build_platform()` with the given runcard dictionary.
        connection (API | None = None): `Qiboconnection's <https://pypi.org/project/qiboconnection>`_ API class used to block access to other users when connected to the platform.

    Examples:

        .. note::

            The following examples contain made up results. These will soon be updated with real results.

        .. note::

            All the following examples are explained in detail in the :ref:`Platform <platform>` section of the documentation. However, here are a few thing to keep in mind:

            - To connect, your computer must be in the same network of the instruments specified in the runcard, with their IP's addresses. Connection is necessary for the subsequent steps.

            - You might want to skip the ``platform.initial_setup()`` and the ``platform.turn_on_instruments()`` steps if you think nothing has been modified, but we recommend doing them every time.

            - ``platform.turn_on_instruments()`` is used to turn on the signal output of all the sources defined in the runcard (RF, Voltage and Current sources).

            - You can print ``platform.chip`` and ``platform.buses`` at any time to check the platform's structure.

        **1. Executing a circuit with Platform:**


        To execute a circuit you first need to define your circuit, for example, one with a pi pulse and a measurement gate in qubit ``q`` (``int``).
        Then you also need to build, connect, set up, and execute the platform, which together look like:

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
        array([[6.],
                [6.]])

        .. note::

            The obtained values correspond to the integral of the I/Q signals received by the digitizer.
            And they have shape `(#sequencers, 2, #bins)`, in this case you only have 1 sequencer and 1 bin.

        You could also get the results in a more standard format, as already classified ``counts`` or ``probabilities`` dictionaries, with:

        >>> result.counts
        {'0': 501, '1': 499}

        >>> result.probabilities
        {'0': .501, '1': .499}

        .. note::

            You can find more information about the results, in the :class:`.Results` class documentation.

        |

        **2. Running a Rabi sweep with Platform:**

        To perform a Rabi sweep, you need the previous circuit, and again, you also need to build, connect and setup the platform.
        But this time, instead than executing the circuit once, you will loop changing the amplitude parameter of the AWG (generator of the pi pulse):

        .. code-block:: python

            # Looping over the AWG amplitude to execute the Rabi sweep:
            results = []
            amp_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 1.0]

            for amp in amp_values:
                platform.set_parameter(alias="drive_q", parameter=ql.Parameter.AMPLITUDE, value=amp)
                result = platform.execute(program=circuit, num_avg=1000, repetition_duration=6000)
                results.append(result.array)

        Now you can use ``np.hstack`` to stack the results horizontally. By doing this, you would obtain an
        array with shape `(2, N)`, where N is the number of elements inside the loop:

        >>> import numpy as np
        >>> np.hstack(results)
        array([[5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3],
                [5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3]])

        You can see how the integrated I/Q values oscillate, indicating that qubit ``q`` oscillates between the ground and
        excited states!

        |

        **3. A faster Rabi sweep, translating the circuit to pulses:**

        Since you are looping over variables that are independent of the circuit (in this case, the amplitude of the AWG),
        you can speed up the experiment by translating the circuit into pulses beforehand, only once, and then, executing the obtained
        pulses inside the loop.

        Which is the same as before, but passing the ``pulse_schedule`` instead than the ``circuit``, to the ``execute()`` method:

        .. code-block:: python

            from qililab.pulse.circuit_to_pulses import CircuitToPulses

            # Translating the circuit to pulses:
            pulse_schedule = CircuitToPulses(platform=platform).translate(circuits=[circuit])

            # Looping over the AWG amplitude to execute the Rabi sweep:
            results = []
            amp_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 1.0]

            for amp in amp_values:
                platform.set_parameter(alias="drive_q", parameter=ql.Parameter.AMPLITUDE, value=amp)
                result = platform.execute(program=pulse_schedule, num_avg=1000, repetition_duration=6000)
                results.append(result.array)

        If you now stack and print the results, you will obtain similar results, but much faster!

        >>> np.hstack(results)
        array([[5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3],
                [5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3]])
        TODO: !!! Change this results for the actual ones !!!

        |

        **4. Ramsey sequence, looping over a parameter inside the circuit:**

        To run a Ramsey sequence you also need to build, connect and set up the platform as before. However, the circuit will be different from the previous one,
        and also, this time, you need to loop over a parameter of the circuit itself, specifically over the time of the ``Wait`` gate.

        To do this, since the parameter is inside the Qibo circuit, you will need to use Qibo own ``circuit.set_parameters()`` method, specifying the
        parameters you want to set, in the same order they appear in the circuit construction:

        .. code-block:: python

            import qililab as ql

            from qibo.models import Circuit
            from qibo import gates

            # Building the platform:
            platform = ql.build_platform(runcard="runcards/galadriel.yml")

            # Connecting and setting up the platform:
            platform.connect()
            platform.initial_setup()
            platform.turn_on_instruments()

            # Defining the Ramsey circuit:
            circuit = Circuit(q + 1)
            circuit.add(gates.RX(q, theta=np.pi/2))
            circuit.add(ql.Wait(q, t=0))
            circuit.add(gates.RX(q, theta=np.pi/2))
            circuit.add(gates.M(q))

            # Looping over the wait time t to execute the Ramsey:
            results = []
            wait_times = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

            for wait in wait_times:
                circuit.set_parameters([np.pi/2, wait, np.pi/2])
                result = platform.execute(program=circuit, num_avg=1000, repetition_duration=6000)
                results.append(result.array)

        which for each execution, would set ``np.pi/2`` to the ``theta`` parameters of the ``RX`` gates, and the looped ``wait`` time  to the ``t`` parameter of the
        ``Wait`` gate.

        If you print the results, you'll see how you obtain the sinusoidal expected behaviour!

        >>> results = np.hstack(results)
        >>> results
        array([[5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3],
                [5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3]])
        TODO: !!! Change this results for the actual sinusoidal ones (change wait_times of execution if needed) !!!
    """

    def __init__(self, runcard: Runcard, connection: API | None = None):
        self.name = runcard.name
        """Name of the platform (``str``) """

        self.device_id = runcard.device_id
        """Device ID of the platform (``int``). This attribute is required for ``qiboconnection`` to save the results remotely."""

        self.gates_settings = runcard.gates_settings
        """Gate settings and definitions (``dataclass``). These setting contain how to decompose gates into pulses."""

        self.instruments = Instruments(elements=self._load_instruments(instruments_dict=runcard.instruments))
        """All the instruments of the platform and their necessary settings (``dataclass``). Each individual instrument is contained in a list within the dataclass."""

        self.instrument_controllers = InstrumentControllers(
            elements=self._load_instrument_controllers(instrument_controllers_dict=runcard.instrument_controllers)
        )
        """All the instrument controllers of the platform and their necessary settings (``dataclass``). Each individual instrument controller is contained in a list within the dataclass."""

        self.chip = Chip(**asdict(runcard.chip))
        """Chip and nodes settings of the platform (:class:`.Chip` dataclass). Each individual node is contained in a list within the :class:`.Chip` class."""

        self.buses = Buses(
            elements=[
                Bus(settings=asdict(bus), platform_instruments=self.instruments, chip=self.chip)
                for bus in runcard.buses
            ]
        )
        """All the buses of the platform and their necessary settings (``dataclass``). Each individual bus is contained in a list within the dataclass."""

        self.connection = connection
        """API ``qiboconnection`` of the platform (``API | None``). It is the same as the passed argument. Defaults to None."""

        self._connected_to_instruments: bool = False
        """Boolean indicating the connection status to the instruments. Defaults to False (not connected)."""

        if any(isinstance(instrument, QbloxModule) for instrument in self.instruments.elements):
            self.compiler = PulseQbloxCompiler(platform=self)  # TODO: integrate with qprogram compiler
            """Compiler to translate given programs to instructions for a given awg vendor."""

        self._qpy_sequence_cache: dict[str, str] = {}
        """Dictionary for caching qpysequences."""

    def connect(self, manual_override=False):
        """Connects to all the instruments and blocks the connection for other users.

        You must be connected in order to set up and turn on instruments, or in order to execute the platform.

        To connect, your computer must be in the same network of the instruments specified in the :ref:`runcard <runcards>` (with their corresponding `device_id` and IP's addresses).

        Such connection is handled via `qiboconnection's <https://pypi.org/project/qiboconnection>`_ `API` in the ``platform.connection`` attribute.

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
        """Sets the values of the cache of the :class:`.Platform` object to the connected instruments.

        If called after a ``ql.build_platform()``, where the :class:`.Platform` object is built with the provided runcard,
        this function sets the values of the :ref:`runcard <runcards>` into the connected instruments.

        It is recommended to use this function after a ``ql.build_platform()`` + ``platform.connect()`` to ensure that no parameter
        differs from the current runcard settings.

        If a `platform.set_parameter()` is called between platform building and initial setup, the value set in the instruments
        will be the new "set" value, as the cache values of the :class:`.Platform` object are modified.
        """
        if not self._connected_to_instruments:
            raise AttributeError("Can not do initial_setup without being connected to the instruments.")
        self.instrument_controllers.initial_setup()
        logger.info("Initial setup applied to the instruments")

    def turn_on_instruments(self):
        """Turns on the signal output for the generator instruments (RF, voltage sources and current sources).

        This does not actually turn on the laboratory instruments, it only opens the signal output generation of the sources.

        We recommend you to do this always after a connection and a setup, to ensure that everything is ready for an execution.
        """
        self.instrument_controllers.turn_on_instruments()
        logger.info("Instruments turned on")

    def turn_off_instruments(self):
        """Turns off the signal output for the generator instruments (local oscillators, voltage sources and current sources).

        This does not actually turn the laboratory instruments off, it only closes their signal output generation.
        """
        self.instrument_controllers.turn_off_instruments()
        logger.info("Instruments turned off")

    def disconnect(self):
        """Closes the connection to all the instruments."""
        if self.connection is not None:
            self.connection.release_device(device_id=self.device_id)
        if not self._connected_to_instruments:
            logger.info("Already disconnected from the instruments")
            return
        self.instrument_controllers.disconnect()
        self._connected_to_instruments = False
        logger.info("Disconnected from instruments")

    def get_element(self, alias: str):
        """Gets the platform element and to which bus it is connected, using its alias.

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

    def get_ch_id_from_qubit_and_bus(self, alias: str, qubit_index: int) -> int | None:
        """Finds a sequencer id for a given qubit given a bus alias. This utility is added so that one can get a qrm's
        channel id easily in case the setup contains more than one qrm and / or there is not a one to one correspondance
        between sequencer id in the instrument and the qubit id. This one to one correspondance used to be the norm for
        5 qubit chips with non-RF QRM modules with 5 sequencers, each mapped to a qubit with the same numerical id as the
        sequencer.
        For QCMs it is also useful since the sequencer id is not always the same as the qubit id.

        Args:
            alias (str): bus alias
            qubit_index (int): qubit index
        Returns:
            int: sequencer id
        """
        bus = next((bus for bus in self._get_bus_by_qubit_index(qubit_index=qubit_index) if bus.alias == alias), None)
        if bus is None:
            raise ValueError(f"Could not find bus with alias {alias} for qubit {qubit_index}")
        if instrument := next(
            (
                instrument
                for instrument in bus.system_control.instruments
                if instrument.name in [InstrumentName.QBLOX_QRM, InstrumentName.QRMRF]
            ),
            None,
        ):
            return next(
                sequencer.identifier for sequencer in instrument.awg_sequencers if sequencer.qubit == qubit_index
            )
        # if the alias is not in the QRMs, it should be in the QCM
        instrument = next(
            instrument
            for instrument in bus.system_control.instruments
            if instrument.name in [InstrumentName.QBLOX_QCM, InstrumentName.QCMRF]
        )
        return next(
            (sequencer.identifier for sequencer in instrument.awg_sequencers if sequencer.chip_port_id == bus.port),
            None,
        )

    def _get_bus_by_qubit_index(self, qubit_index: int) -> tuple[Bus, Bus, Bus]:
        """Finds buses associated with the given qubit index.

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
        return flux_bus, control_bus, readout_bus

    def _get_bus_by_alias(self, alias: str | None = None):
        """Gets buses given their alias.

        Args:
            alias (str | None, optional): Bus alias to identify it. Defaults to None.

        Returns:
            :class:`Bus`: Bus corresponding to the given alias. If none is found `None` is returned.

        """
        return next((bus for bus in self.buses if bus.alias == alias), None)

    def get_parameter(self, parameter: Parameter, alias: str, channel_id: int | None = None):
        """Get platform parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            alias (str): Alias of the bus where the parameter is set.
            channel_id (int, optional): ID of the channel we want to use to set the parameter. Defaults to None.
        """
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        if alias == "platform" or regex_match is not None:
            return self.gates_settings.get_parameter(alias=alias, parameter=parameter, channel_id=channel_id)
        element = self.get_element(alias=alias)
        return element.get_parameter(parameter=parameter, channel_id=channel_id)

    def set_parameter(
        self,
        parameter: Parameter,
        value: float | str | bool,
        alias: str,
        channel_id: int | None = None,
    ):
        """Set a parameter for a platform element.

        If connected to an instrument, this function updates both the cache of the :class:`.Platform` object and the
        instrument's value. Otherwise, it only stores the value in the cache. Subsequent ``connect()`` + ``initial_setup()``
        will apply the cached values into the real instruments.

        If you use ``set_parameter`` + ``ql.save_platform()``, the saved runcard will include the new "set" value, even without
        an instrument connection, as the cache values of the :class:`.Platform` object are modified.

        Args:
            parameter (Parameter): Name of the parameter to change.
            value (float | str | bool): New value to set in the parameter.
            alias (str): Alias of the bus where the parameter is set.
            channel_id (int, optional): ID of the channel you want to use to set the parameter. Defaults to None.
        """
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        if alias == "platform" or regex_match is not None:
            self.gates_settings.set_parameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id)
            return
        element = self.get_element(alias=alias)
        element.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def _load_instruments(self, instruments_dict: list[dict]) -> list[Instrument]:
        """Instantiates all instrument classes from their respective dictionaries.

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
        """Instantiates all instrument controller classes from their respective dictionaries.

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
        """Returns all platform information as a dictionary, called the :ref:`runcard <runcards>`. Used for the platform serialization.

        Returns:
            dict: Dictionary of the serialized platform
        """
        name_dict = {RUNCARD.NAME: self.name}
        device_id = {RUNCARD.DEVICE_ID: self.device_id}
        gates_settings_dict = {RUNCARD.GATES_SETTINGS: self.gates_settings.to_dict()}
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
        return str(YAML().dump(self.to_dict(), io.BytesIO()))

    def execute_qprogram(
        self, qprogram: QProgram, bus_mapping: dict[str, str] | None = None, debug: bool = False
    ) -> QProgramResults:
        """Execute a QProgram using the platform instruments.

        Args:
            qprogram (QProgram): The QProgram to execute.

        Returns:
            dict[str, list[Result]]: A dictionary of measurement results. The keys correspond to the buses a measurement were performed upon, and the values are the list of measurement results in chronological order.
        """
        bus_aliases = {bus_mapping[bus] if bus_mapping and bus in bus_mapping else bus for bus in qprogram.buses}
        buses = [self._get_bus_by_alias(alias=bus_alias) for bus_alias in bus_aliases]
        instruments = {
            instrument
            for bus in buses
            for instrument in bus.system_control.instruments
            if isinstance(instrument, (QbloxModule, QuantumMachinesCluster))
        }
        if all(isinstance(instrument, QbloxModule) for instrument in instruments):
            return self._execute_qprogram_with_qblox(qprogram=qprogram, bus_mapping=bus_mapping, debug=debug)
        if all(isinstance(instrument, QuantumMachinesCluster) for instrument in instruments):
            if len(instruments) != 1:
                raise NotImplementedError(
                    "Executing QProgram in more than one Quantum Machines Cluster is not supported."
                )
            cluster: QuantumMachinesCluster = instruments.pop()  # type: ignore[assignment]
            return self._execute_qprogram_with_quantum_machines(
                cluster=cluster, qprogram=qprogram, bus_mapping=bus_mapping, debug=debug
            )
        raise NotImplementedError("Executing QProgram in a mixture of instruments is not supported.")

    def _execute_qprogram_with_qblox(
        self, qprogram: QProgram, bus_mapping: dict[str, str] | None = None, debug: bool = False
    ) -> QProgramResults:
        # Compile QProgram
        qblox_compiler = QbloxCompiler()
        sequences = qblox_compiler.compile(qprogram=qprogram, bus_mapping=bus_mapping)
        buses = {bus_alias: self._get_bus_by_alias(alias=bus_alias) for bus_alias in sequences}

        if debug:
            with open("debug_qblox_execution.txt", "w", encoding="utf-8") as sourceFile:
                for bus_alias in sequences:
                    print(f"Bus {bus_alias}:", file=sourceFile)
                    print(str(sequences[bus_alias]._program), file=sourceFile)  # pylint: disable=protected-access
                    print(file=sourceFile)

        # Upload sequences
        for bus_alias in sequences:
            sequence_hash = hash_qpy_sequence(sequence=sequences[bus_alias])
            if bus_alias not in self._qpy_sequence_cache or self._qpy_sequence_cache[bus_alias] != sequence_hash:
                buses[bus_alias].upload_qpysequence(qpysequence=sequences[bus_alias])
                self._qpy_sequence_cache[bus_alias] = sequence_hash
            # sync all rellevant sequences
            for instrument in buses[bus_alias].system_control.instruments:
                if isinstance(instrument, QbloxModule):
                    instrument.sync_by_port(buses[bus_alias].port)

        # Execute sequences
        for bus_alias in sequences:
            buses[bus_alias].run()

        # Acquire results
        results = QProgramResults()
        for bus_alias in buses:
            if isinstance(buses[bus_alias].system_control, ReadoutSystemControl):
                acquisitions = list(sequences[bus_alias].todict()["acquisitions"])
                bus_results = buses[bus_alias].acquire_qprogram_results(acquisitions=acquisitions)
                for bus_result in bus_results:
                    results.append_result(bus=bus_alias, result=bus_result)

        # Reset instrument settings
        for bus_alias in sequences:
            for instrument in buses[bus_alias].system_control.instruments:
                if isinstance(instrument, QbloxModule):
                    instrument.desync_by_port(buses[bus_alias].port)

        return results

    def _execute_qprogram_with_quantum_machines(  # pylint: disable=too-many-locals
        self,
        cluster: QuantumMachinesCluster,
        qprogram: QProgram,
        bus_mapping: dict[str, str] | None = None,
        debug: bool = False,
    ) -> QProgramResults:
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(qprogram=qprogram, bus_mapping=bus_mapping)

        cluster.append_configuration(configuration=configuration)

        if debug:
            with open("debug_qm_execution.py", "w", encoding="utf-8") as sourceFile:
                print(generate_qua_script(qua_program, cluster.config), file=sourceFile)

        compiled_program_id = cluster.compile(program=qua_program)
        job = cluster.run_compiled_program(compiled_program_id=compiled_program_id)

        acquisitions = cluster.get_acquisitions(job=job)

        results = QProgramResults()
        for measurement in measurements:
            measurement_result = QuantumMachinesMeasurementResult(
                *[acquisitions[handle] for handle in measurement.result_handles]
            )
            results.append_result(bus=measurement.bus, result=measurement_result)

        return results

    def execute(
        self,
        program: PulseSchedule | Circuit,
        num_avg: int,
        repetition_duration: int,
        num_bins: int = 1,
        queue: Queue | None = None,
    ) -> Result | QbloxResult:
        """Compiles and executes a circuit or a pulse schedule, using the platform instruments.

        If the ``program`` argument is a :class:`Circuit`, it will first be translated into a :class:`PulseSchedule` using the transpilation
        settings of the platform. Then the pulse schedules will be compiled into the assembly programs and executed.

        To compile to assembly programs, the ``platform.compile()`` method is called; check its documentation for more information.

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
        readout_buses = [
            bus for bus in self.buses if isinstance(bus.system_control, ReadoutSystemControl) and bus.alias in programs
        ]
        results: list[Result] = []
        for bus in readout_buses:
            result = bus.acquire_result()
            if queue is not None:
                queue.put_nowait(item=result)
            if not np.all(np.isnan(result.array)):
                results.append(result)

        for instrument in self.instruments.elements:
            if isinstance(instrument, QbloxModule):
                instrument.desync_sequencers()

        # Flatten results if more than one readout bus was used for a qblox module
        if len(results) > 1:
            results = [
                QbloxResult(
                    integration_lengths=[length for result in results for length in result.integration_lengths],  # type: ignore [attr-defined]
                    qblox_raw_results=[raw_result for result in results for raw_result in result.qblox_raw_results],  # type: ignore [attr-defined]
                )
            ]
        if not results:
            raise ValueError("There are no readout buses in the platform.")

        if isinstance(program, Circuit):
            results = [self._order_result(results[0], program)]

        # FIXME: resurn result instead of results[0]
        return results[0]

    def _order_result(self, result: Result, circuit: Circuit) -> Result:
        """Order the results of the execution as they are ordered in the input circuit.
        Finds the absolute order of each measurement for each qubit and its corresponding key in the
        same format as in qblox's aqcuisitions dictionary (#qubit, #qubit_measurement).
        Then it orders results in the same measurement order as the one in circuit.queue.
        Args:
            result (Result): Result obtained from the execution
            circuit (Circuit): qibo circuit being executed
        Returns:
            Result: Result obtained from the execution, with each measurement in the same order as in circuit.queue
        """
        if not isinstance(result, QbloxResult):
            raise NotImplementedError("Result ordering is only implemented for qblox results")

        # register the overall order of all qubit measurements.
        qubits_m = {}
        order = {}
        # iterate over qubits measured in same order as they appear in the circuit
        for i, qubit in enumerate(qubit for gate in circuit.queue for qubit in gate.qubits if isinstance(gate, M)):
            if qubit not in qubits_m:
                qubits_m[qubit] = 0
            order[(qubit, qubits_m[qubit])] = i
            qubits_m[qubit] += 1
        if len(order) != len(result.qblox_raw_results):
            raise ValueError(
                f"Number of measurements in the circuit {len(order)} does not match number of acquisitions {len(result.qblox_raw_results)}"
            )

        # allocate each measurement its corresponding index in the results list
        results = [None] * len(order)  # type: list | list[dict]
        for qblox_result in result.qblox_raw_results:
            measurement = qblox_result["measurement"]
            qubit = qblox_result["qubit"]
            results[order[(qubit, measurement)]] = qblox_result

        return QbloxResult(integration_lengths=result.integration_lengths, qblox_raw_results=results)

    def compile(
        self, program: PulseSchedule | Circuit, num_avg: int, repetition_duration: int, num_bins: int
    ) -> dict[str, list[QpySequence]]:
        """Compiles the circuit / pulse schedule into a set of assembly programs, to be uploaded into the awg buses.

        If the ``program`` argument is a :class:`Circuit`, it will first be translated into a :class:`PulseSchedule` using the transpilation
        settings of the platform. Then the pulse schedules will be compiled into the assembly programs.

        This methods gets called during the ``platform.execute()`` method, check its documentation for more information.

        Args:
            program (:class:`PulseSchedule` | :class:`Circuit`): Circuit or pulse schedule to compile.
            num_avg (int): Number of hardware averages used.
            repetition_duration (int): Minimum duration of a single execution.
            num_bins (int): Number of bins used.

        Returns:
            dict: Dictionary of compiled assembly programs. The key is the bus alias (``str``), and the value is the assembly compilation (``list``).

        Raises:
            ValueError: raises value error if the circuit execution time is longer than ``repetition_duration`` for some qubit.
        """
        # We have a circular import because Platform uses CircuitToPulses and vice versa

        if isinstance(program, Circuit):
            transpiler = CircuitTranspiler(platform=self)
            pulse_schedule = transpiler.transpile_circuit(circuits=[program])[0]
        elif isinstance(program, PulseSchedule):
            pulse_schedule = program
        else:
            raise ValueError(
                f"Program to execute can only be either a single circuit or a pulse schedule. Got program of type {type(program)} instead"
            )
        return self.compiler.compile(
            pulse_schedule=pulse_schedule, num_avg=num_avg, repetition_duration=repetition_duration, num_bins=num_bins
        )
