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

from __future__ import annotations

import ast
import io
import re
import tempfile
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Callable, cast

from qm import generate_qua_script
from ruamel.yaml import YAML
from rustworkx import PyGraph

from qililab.analog import AnnealingProgram
from qililab.config import logger
from qililab.constants import FLUX_CONTROL_REGEX, GATE_ALIAS_REGEX, RUNCARD
from qililab.digital import CircuitToQProgramCompiler, CircuitTranspiler
from qililab.exceptions import ExceptionGroup
from qililab.instrument_controllers import InstrumentController, InstrumentControllers
from qililab.instrument_controllers.utils import InstrumentControllerFactory
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.instruments.qblox import QbloxModule
from qililab.instruments.qblox.qblox_draw import QbloxDraw
from qililab.instruments.quantum_machines import QuantumMachinesCluster
from qililab.instruments.utils import InstrumentFactory
from qililab.platform.components.bus import Bus
from qililab.platform.components.buses import Buses
from qililab.qprogram import (
    Calibration,
    Domain,
    Experiment,
    QbloxCompilationOutput,
    QbloxCompiler,
    QProgram,
    QuantumMachinesCompilationOutput,
    QuantumMachinesCompiler,
)
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix, FluxVector
from qililab.qprogram.experiment_executor import ExperimentExecutor
from qililab.result.database import get_db_manager
from qililab.result.qprogram.qprogram_results import QProgramResults
from qililab.result.qprogram.quantum_machines_measurement_result import QuantumMachinesMeasurementResult
from qililab.result.stream_results import StreamArray
from qililab.typings import ChannelID, InstrumentName, Parameter, ParameterValue
from qililab.utils import hash_qpy_sequence

if TYPE_CHECKING:
    import numpy as np
    from qilisdk.digital import Circuit

    from qililab.digital import DigitalTranspilationConfig
    from qililab.instrument_controllers.instrument_controller import InstrumentController
    from qililab.instruments.instrument import Instrument
    from qililab.result.database import DatabaseManager
    from qililab.settings import Runcard
    from qililab.settings.digital.gate_event_settings import GateEventSettings


class Platform:
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

    >>> platform.connect()  # Connects to all the instruments.
    >>> platform.initial_setup()  # Sets the parameters defined in the runcard.
    >>> platform.turn_on_instruments()  # Turns on the signal outputs.

    And then, for each experiment you want to run, you would typically repeat:

    >>> platform.set_parameter(...)  # Sets any parameter of the Platform.
    >>> result = platform.execute(...)  # Executes the platform.

    Args:
        runcard (Runcard): Dataclass containing the serialized platform (chip, instruments, buses...), created during :meth:`ql.build_platform()` with the given runcard dictionary.

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
            circuit = Circuit(q + 1)
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
            circuit.add(gates.RX(q, theta=np.pi / 2))
            circuit.add(ql.Wait(q, t=0))
            circuit.add(gates.RX(q, theta=np.pi / 2))
            circuit.add(gates.M(q))

            # Looping over the wait time t to execute the Ramsey:
            results = []
            wait_times = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

            for wait in wait_times:
                circuit.set_parameters([np.pi / 2, wait, np.pi / 2])
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

    def __init__(self, runcard: Runcard):
        self.name = runcard.name
        """Name of the platform (``str``) """

        self.instruments = Instruments(elements=self._load_instruments(instruments_dict=runcard.instruments))
        """All the instruments of the platform and their necessary settings (``dataclass``). Each individual instrument is contained in a list within the dataclass."""

        self.instrument_controllers = InstrumentControllers(
            elements=self._load_instrument_controllers(instrument_controllers_dict=runcard.instrument_controllers)
        )
        """All the instrument controllers of the platform and their necessary settings (``dataclass``). Each individual instrument controller is contained in a list within the dataclass."""

        self.buses = Buses(
            elements=[Bus(settings=asdict(bus), platform_instruments=self.instruments) for bus in runcard.buses]
        )
        """All the buses of the platform and their necessary settings (``dataclass``). Each individual bus is contained in a list within the dataclass."""

        self.digital_compilation_settings = runcard.digital
        """Gate settings and definitions (``dataclass``). These setting contain how to decompose gates into pulses."""

        self.analog_compilation_settings = runcard.analog
        """Flux to bus mapping for analog control"""

        self._connected_to_instruments: bool = False
        """Boolean indicating the connection status to the instruments. Defaults to False (not connected)."""

        self._qpy_sequence_cache: dict[str, str] = {}
        """Dictionary for caching qpysequences."""

        self.experiment_results_base_path: str = tempfile.gettempdir()
        """Base path for saving experiment results."""

        self.experiment_results_path_format: str = "{date}/{time}/{label}.h5"
        """Format of the experiment results path."""

        self.crosstalk: CrosstalkMatrix | None = None
        """Crosstalk matrix information, defaults to None (only used on FLUX parameters)"""

        self.flux_vector: FluxVector | None = None
        """Flux vector information, defaults to None (only used on FLUX parameters)"""

        self.flux_parameter: dict[str, int | float | bool | str] = {}
        """Flux dictionary with information for the get parameter (only used on FLUX parameters)"""

        self.db_manager: DatabaseManager | None = None
        """Database manager for experiment class and db stream array"""

        self.save_experiment_results_in_database: bool = True
        """Database trigger to define if the experiment metadata will be saved in a database or not"""

    def connect(self):
        """Connects to all the instruments and blocks the connection for other users.

        You must be connected in order to set up and turn on instruments, or in order to execute the platform.

        To connect, your computer must be in the same network of the instruments specified in the :ref:`runcard <runcards>` (with their corresponding IP's addresses).
        """
        if self._connected_to_instruments:
            logger.info("Already connected to the instruments")
            return

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
        if not self._connected_to_instruments:
            logger.info("Already disconnected from the instruments")
            return
        self.instrument_controllers.disconnect()
        self._connected_to_instruments = False
        self._qpy_sequence_cache = {}
        logger.info("Disconnected from instruments")

    def get_element(self, alias: str):
        """Gets the platform element and to which bus it is connected, using its alias.

        Args:
            alias (str): Element alias to identify it.

        Returns:
            tuple[object, list | None]: Element class together with the index of the bus where the element is located.
        """
        # TODO: fix docstring, bus is not returned in most cases
        regex_match = re.search(GATE_ALIAS_REGEX, alias.split("_")[0])
        if regex_match is not None:
            name = regex_match["gate"]
            qubits_str = regex_match["qubits"]
            qubits = ast.literal_eval(qubits_str)
            if (
                self.digital_compilation_settings is not None
                and f"{name}({qubits_str})" in self.digital_compilation_settings.gate_names
            ):
                return self.digital_compilation_settings.get_gate(name=name, qubits=qubits)
        regex_match = re.search(FLUX_CONTROL_REGEX, alias)
        if regex_match is not None:
            element_type = regex_match.lastgroup
            element_shorthands = {"qubit": "q", "coupler": "c"}
            flux = regex_match["flux"]
            # TODO: support commuting the name of the coupler eg. c1_0 = c0_1
            bus_alias = next(
                (
                    element.bus
                    for element in self.analog_compilation_settings.flux_control_topology  # type: ignore[union-attr]
                    if self.analog_compilation_settings
                    and element.flux == f"{flux}_{element_shorthands[element_type]}{regex_match[element_type]}"  # type: ignore[index]
                ),
                None,
            )
            if bus_alias is not None:
                return self.buses.get(alias=bus_alias)

        element = self.instruments.get_instrument(alias=alias)
        if element is None:
            element = self.instrument_controllers.get_instrument_controller(alias=alias)
        if element is None:
            element = self.buses.get(alias=alias)
        return element

    def _get_bus_by_alias(self, alias: str) -> Bus | None:
        """Gets buses given their alias.

        Args:
            alias (str, optional): Bus alias to identify it. Defaults to None.

        Returns:
            :class:`Bus`: Bus corresponding to the given alias. If none is found `None` is returned.

        """
        return self.buses.get(alias=alias)

    def get_parameter(self, alias: str, parameter: Parameter, channel_id: ChannelID | None = None):
        """Get platform parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            alias (str): Alias of the bus where the parameter is set.
            channel_id (int, optional): ID of the channel we want to use to set the parameter. Defaults to None.
        """
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        if alias == "platform" or parameter == Parameter.DELAY or regex_match is not None:
            if self.digital_compilation_settings is None:
                raise ValueError("Trying to get parameter of gates settings, but no gates settings exist in platform.")
            return self.digital_compilation_settings.get_parameter(
                alias=alias, parameter=parameter, channel_id=channel_id
            )
        if parameter == Parameter.FLUX:
            if alias not in self.flux_parameter:
                self.flux_parameter[alias] = 0.0
            return self.flux_parameter[alias]
        element = self.get_element(alias=alias)
        return element.get_parameter(parameter=parameter, channel_id=channel_id)

    def _data_draw(self):
        """From the runcard retrieve the parameters necessary to draw the qprogram."""
        data_oscilloscope = {}
        buses = list(self.buses)
        instruments = {
            instrument for bus in buses for instrument in bus.instruments if isinstance(instrument, (QbloxModule))
        }
        if instruments and all(isinstance(instrument, QbloxModule) for instrument in instruments):
            for bus in buses:
                for instrument, _ in zip(bus.instruments, bus.channels):
                    if isinstance(instrument, QbloxModule):
                        data_oscilloscope[bus.alias] = {}
                        dac_offset_i = 0
                        dac_offset_q = 0
                        parameters = [
                            Parameter.IF,
                            Parameter.GAIN_I,
                            Parameter.GAIN_Q,
                            Parameter.OFFSET_I,
                            Parameter.OFFSET_Q,
                            Parameter.HARDWARE_MODULATION,
                        ]
                        for parameter in parameters:
                            data_oscilloscope[bus.alias][parameter.value] = self.get_parameter(bus.alias, parameter)

                        data_oscilloscope[bus.alias]["instrument_name"] = instrument.name.value

                        if instrument.name == InstrumentName.QBLOX_QCM or instrument.name == InstrumentName.QBLOX_QRM:
                            # retrieve the dac offset and assign it to the bus
                            identifier = bus.channels
                            for awg in instrument.awg_sequencers:
                                if awg.identifier == identifier[0]:
                                    for idx, out in enumerate(awg.outputs):
                                        if idx == 0:
                                            dac_offset_i = instrument.out_offsets[out]
                                        elif idx == 1:
                                            dac_offset_q = instrument.out_offsets[out]
                            data_oscilloscope[bus.alias]["dac_offset_i"] = dac_offset_i
                            data_oscilloscope[bus.alias]["dac_offset_q"] = dac_offset_q

                        elif instrument.name == InstrumentName.QCMRF or instrument.name == InstrumentName.QRMRF:
                            # retrieve the dac offset and assign it to the bus
                            identifier = bus.channels
                            for awg in instrument.awg_sequencers:
                                if awg.identifier == identifier[0]:
                                    for out in awg.outputs:
                                        if out == 0:
                                            dac_offset_i = bus.get_parameter(Parameter.OUT0_OFFSET_PATH0)
                                            dac_offset_q = bus.get_parameter(Parameter.OUT0_OFFSET_PATH1)
                                        elif out == 1:
                                            dac_offset_i = bus.get_parameter(Parameter.OUT1_OFFSET_PATH0)
                                            dac_offset_q = bus.get_parameter(Parameter.OUT1_OFFSET_PATH1)

                            data_oscilloscope[bus.alias]["dac_offset_i"] = dac_offset_i
                            data_oscilloscope[bus.alias]["dac_offset_q"] = dac_offset_q

        else:
            # TODO: the same information could be generated with a Quantum Machine runcard, even if the QBlox Compiler is used in the background.
            raise NotImplementedError("The drawing feature is currently only supported for QBlox.")

        return data_oscilloscope

    def set_parameter(
        self,
        alias: str,
        parameter: Parameter,
        value: ParameterValue,
        channel_id: ChannelID | None = None,
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
        if alias == "platform" or parameter == Parameter.DELAY or regex_match is not None:
            if self.digital_compilation_settings is None:
                raise ValueError("Trying to get parameter of gates settings, but no gates settings exist in platform.")
            self.digital_compilation_settings.set_parameter(
                alias=alias, parameter=parameter, value=value, channel_id=channel_id
            )
            return

        element = self.get_element(alias=alias)

        if parameter == Parameter.FLUX:
            self.flux_parameter[alias] = float(value)
            self._process_crosstalk(alias, value)
            self._set_bias_from_element(element)
            return

        element.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def _set_bias_from_element(self, element: list[GateEventSettings] | Bus | InstrumentController | Instrument | None):  # type: ignore[union-attr]
        """Sets the right parameter depending on the instrument defined inside the element.
        This is used in the crosstalk correction.
        The instruments included in this function are: QM, QBlox, SPI and QDevil.

        Args:
            element (_type_): runcard elemnt.

        """
        bias = [
            instrument
            for instrument in element.instruments  # type: ignore[union-attr]
            if instrument.name
            in {"QCM", "QRM", "QRM-RF", "QCM-RF", "D5a", "S4g", "quantum_machines_cluster", "qdevil_qdac2"}
        ]

        if len(bias) == 0:
            raise ReferenceError(
                "Flux bus must have one of these instruments:\nQCM, QRM, QRM-RF, QCM-RF, D5a, S4g, quantum_machines_cluster, qdevil_qdac2"
            )
        if len(bias) > 1:
            raise NotImplementedError(
                "Flux bus must not have more than one of these instruments:\nQCM, QRM, QRM-RF, QCM-RF, D5a, S4g, quantum_machines_cluster, qdevil_qdac2"
            )
        if bias[0].name in {"quantum_machines_cluster"}:
            parameter = Parameter.DC_OFFSET
        if bias[0].name in {"D5a", "qdevil_qdac2"}:
            parameter = Parameter.VOLTAGE
        if bias[0].name in {"S4g"}:
            parameter = Parameter.CURRENT
        for flux_alias, flux_value in self.flux_vector.bias_vector.items():  # type: ignore[union-attr]
            flux_element = self.get_element(alias=flux_alias)
            if bias[0].name in {"QCM", "QRM", "QRM-RF", "QCM-RF"}:
                offset_channel = flux_element.instruments[0].awg_sequencers[flux_element.channels[0]].outputs[0]
                if offset_channel == 0:
                    parameter = Parameter.OFFSET_OUT0
                if offset_channel == 1:
                    parameter = Parameter.OFFSET_OUT1
                if offset_channel == 2:
                    parameter = Parameter.OFFSET_OUT2
                if offset_channel == 3:
                    parameter = Parameter.OFFSET_OUT3
            flux_element.set_parameter(parameter=parameter, value=flux_value)
        return

    def _process_crosstalk(self, alias: str, value):
        """Calculates the Current/Voltage of the set parameter based on the value of the flux and the crosstalk matrix"""
        if not self.crosstalk:
            raise ValueError("Crosstalk matrix has not been set")

        bus_list = list(self.crosstalk.matrix.keys())

        if not self.flux_vector:
            self.flux_vector = FluxVector()
        for flux in bus_list:
            if flux not in self.flux_vector.flux_vector.keys():
                self.flux_vector[flux] = 0

        if alias not in self.crosstalk.matrix.keys():
            raise ValueError(f"{alias} not inside crosstalk matrix\n{self.crosstalk}")

        if not self.flux_vector.crosstalk or self.crosstalk != self.flux_vector.crosstalk:
            self.flux_vector.set_crosstalk(self.crosstalk)

        self.flux_vector[alias] = value

    def set_crosstalk(self, crosstalk: CrosstalkMatrix):
        """Sets the crosstalk matrix using the crosstalk matrix class.

        Args:
            crosstalk (CrosstalkMatrix): Crosstalk matrix to implement on the sample
        """
        self.crosstalk = crosstalk

    def set_flux_to_zero(self, bus_list: list[str] | None = None):
        """Set all lines inside the crosstalk / bus list to 0 Phi0, sets everything into the crosstalk offsets.

        Args:
            bus_list (list[str] | None, optional): Optional bus list for all the flux used in the experiment. Defaults to the Crosstalk buses.
        """
        if not self.crosstalk:
            raise ValueError("Crosstalk matrix has not been set")

        if not bus_list:
            bus_list = list(self.crosstalk.matrix.keys())

        for flux_alias in bus_list:
            self.set_parameter(alias=flux_alias, parameter=Parameter.FLUX, value=0)

    def set_bias_to_zero(self, bus_list: list[str] | None = None):
        """Set all lines inside the crosstalk / bus list to 0 Volts / Amperes.

        Args:
            bus_list (list[str] | None, optional): Optional bus list for all the flux used in the experiment. Defaults to the Crosstalk buses.
        """

        if not bus_list:
            if not self.crosstalk:
                raise ValueError("Neither crosstalk matrix nor bus_list has been set")
            bus_list = list(self.crosstalk.matrix.keys())

        if not self.flux_vector:
            self.flux_vector = FluxVector()
        for flux in bus_list:
            if flux not in self.flux_vector.flux_vector.keys():
                self.flux_vector[flux] = 0

        for flux_alias in bus_list:
            element = self.get_element(alias=flux_alias)
            self._set_bias_from_element(element)

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
        instrument_dict = {RUNCARD.INSTRUMENTS: self.instruments.to_dict()}
        instrument_controllers_dict = {RUNCARD.INSTRUMENT_CONTROLLERS: self.instrument_controllers.to_dict()}
        buses_dict = {RUNCARD.BUSES: self.buses.to_dict()}
        digital_dict = {
            RUNCARD.DIGITAL: (
                self.digital_compilation_settings.to_dict() if self.digital_compilation_settings is not None else None
            )
        }
        analog_dict = {
            RUNCARD.ANALOG: (
                self.analog_compilation_settings.to_dict() if self.analog_compilation_settings is not None else None
            )
        }

        return name_dict | instrument_dict | instrument_controllers_dict | buses_dict | digital_dict | analog_dict

    def __str__(self) -> str:
        """String representation of the platform.

        Returns:
            str: Name of the platform.
        """
        return str(YAML(typ="safe").dump(self.to_dict(), io.BytesIO()))

    @contextmanager
    def session(self):
        """Context manager to manage platform session, ensuring that resources are always released."""
        cleanup_methods = []
        cleanup_errors = []
        try:
            # Track successfully called setup methods and their cleanup counterparts
            self.connect()
            cleanup_methods.append(self.disconnect)  # Store disconnect for cleanup

            self.initial_setup()  # No specific cleanup for initial_setup

            self.turn_on_instruments()
            cleanup_methods.append(self.turn_off_instruments)  # Store turn_off_instruments for cleanup

            yield  # Experiment logic goes here

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise  # Re-raise the exception for further handling
        finally:
            # Call the cleanup methods in reverse order
            for cleanup_method in reversed(cleanup_methods):
                try:
                    cleanup_method()
                except Exception as e:  # noqa: BLE001
                    logger.error(f"Error during cleanup: {e}")
                    cleanup_errors.append(e)

            # Raise any exception that might have happened during cleanup
            if cleanup_errors:
                raise ExceptionGroup("Exceptions occurred during cleanup", cleanup_errors)

    def compile_annealing_program(
        self,
        annealing_program_dict: list[dict[str, dict[str, float]]],
        transpiler: Callable,
        calibration: Calibration,
        num_averages: int = 1000,
        num_shots: int = 1,
        preparation_block: str = "preparation",
        measurement_block: str = "measurement",
    ) -> QProgram:
        """
        Compile an annealing program into a `QProgram` by mapping Ising coefficients to flux waveforms.

        This method takes an annealing program, represented as a time-ordered list of circuit elements with
        corresponding Ising coefficients, and compiles it into a quantum program (QProgram) that can be
        executed on a quantum annealing hardware setup.

        The input `annealing_program_dict` is structured as a list of dictionaries, each representing a
        specific time point. Each dictionary maps qubit and coupler identifiers to Ising terms (`sigma_x`,
        `sigma_y`, `sigma_z`), indicating the coefficient values for each term. For example:

        .. code-block:: python

            [
                {"qubit_0": {"sigma_x": 0, "sigma_y": 1, "sigma_z": 2}, "coupler_1_0": {...}},
                {...},  # time=1ns
                ...,
            ]

        Using the provided `transpiler`, these Ising coefficients are converted to flux values. These fluxes
        are then transformed into waveforms assigned to specific hardware buses, as defined by a `flux_to_bus`
        mapping in the analog compilation settings.

        Args:
            annealing_program_dict (list[dict[str, dict[str, float]]]): The time-ordered list of qubit and
                coupler Ising coefficients to be compiled.
            transpiler (Callable): A function to convert Ising parameters (delta, epsilon) to flux values
                (phix, phiz).
            calibration (Calibration): Calibration data containing the required blocks (e.g., `preparation`,
                `measurement`) and any applicable crosstalk corrections.
            num_averages (int, optional): Number of times the program should be averaged per shot. Defaults to 1000.
            num_shots (int, optional): Number of shots to execute the program. Defaults to 1.
            preparation_block (str, optional): Name of the calibration block used for preparation. Defaults to "preparation".
            measurement_block (str, optional): Name of the calibration block used for measurement. Defaults to "measurement".

        Returns:
            QProgram: A compiled quantum program (QProgram) ready for execution on the target hardware.

        Raises:
            ValueError: If the flux-to-bus topology is not defined in the analog compilation settings.
            ValueError: If the specified `measurement_block` is not available in the calibration.

        Notes:
            - The method checks for essential compilation settings and calibrated blocks, ensuring the program can be executed successfully.
            - Transpiled waveforms are adjusted for crosstalk when a crosstalk matrix is available in the calibration.
            - Execution includes optional `preparation_block` and synchronizes waveforms before the final `measurement_block`.

        """
        if self.analog_compilation_settings is None:
            raise ValueError("Flux to bus topology not given in the runcard")

        if not calibration.has_block(name=measurement_block):
            raise ValueError("The calibrated measurement is not present in the calibration file.")

        annealing_program = AnnealingProgram(
            flux_to_bus_topology=self.analog_compilation_settings.flux_control_topology,
            annealing_program=annealing_program_dict,
        )
        annealing_program.transpile(transpiler)
        crosstalk_matrix = calibration.crosstalk_matrix.inverse() if calibration.crosstalk_matrix is not None else None
        annealing_waveforms = annealing_program.get_waveforms(crosstalk_matrix=crosstalk_matrix, minimum_clock_time=4)

        qp_annealing = QProgram()
        shots_variable = qp_annealing.variable("num_shots", Domain.Scalar, int)

        with qp_annealing.for_loop(variable=shots_variable, start=0, stop=num_shots, step=1):
            with qp_annealing.average(num_averages):
                if calibration.has_block(name=preparation_block):
                    qp_annealing.insert_block(calibration.get_block(name=preparation_block))
                    qp_annealing.sync()
                for bus, waveform in annealing_waveforms.items():
                    qp_annealing.play(bus=bus, waveform=waveform)
                qp_annealing.sync()
                qp_annealing.insert_block(calibration.get_block(name=measurement_block))

        return qp_annealing

    def execute_annealing_program(
        self,
        annealing_program_dict: list[dict[str, dict[str, float]]],
        transpiler: Callable,
        calibration: Calibration,
        num_averages: int = 1000,
        num_shots: int = 1,
        preparation_block: str = "preparation",
        measurement_block: str = "measurement",
        bus_mapping: dict[str, str] | None = None,
        debug: bool = False,
    ) -> QProgramResults:
        """Given an annealing program execute it as a qprogram.
        The annealing program should contain a time ordered list of circuit elements and their corresponging ising coefficients as a dictionary. Example structure:

        .. code-block:: python

            [
                {"qubit_0": {"sigma_x" : 0, "sigma_y" : 1, "sigma_z" : 2},
                "coupler_1_0 : {...},
                },      # time=0ns
                {...},  # time=1ns
            .
            .
            .
            ]

        This dictionary containing ising coefficients is transpiled to fluxes using the given transpiler. Then the correspoinding waveforms are obtained and assigned to a bus
        from the bus to flux mapping given by the runcard.

        Args:
            annealing_program_dict (list[dict[str, dict[str, float]]]): annealing program to run
            transpiler (Callable): ising to flux transpiler. The transpiler should take 2 values as arguments (delta, epsilon) and return 2 values (phix, phiz)
            averages (int, optional): Amount of times to run and average the program over. Defaults to 1.
            debug (bool, optional): Whether to create debug information. For ``Qblox`` clusters all the program information is printed on screen.
                For ``Quantum Machines`` clusters a ``.py`` file is created containing the ``QUA`` and config compilation. Defaults to False.
        """

        qprogram = self.compile_annealing_program(
            annealing_program_dict=annealing_program_dict,
            transpiler=transpiler,
            calibration=calibration,
            num_averages=num_averages,
            num_shots=num_shots,
            preparation_block=preparation_block,
            measurement_block=measurement_block,
        )
        return self.execute_qprogram(qprogram=qprogram, calibration=calibration, bus_mapping=bus_mapping, debug=debug)

    def execute_experiment(
        self,
        experiment: Experiment,
        live_plot: bool = True,
        slurm_execution: bool = True,
        port_number: int | None = None,
    ) -> str:
        """Executes a quantum experiment on the platform.

        This method manages the execution of a given `Experiment` on the platform by utilizing an `ExperimentExecutor`. It orchestrates the entire process, including traversing the experiment's structure, handling loops and operations, and streaming results in real-time to ensure data integrity. The results are saved in a timestamped directory within the specified `base_data_path`.

        Args:
            experiment (Experiment): The experiment object defining the sequence of operations and loops.
            live_plot (bool): Flag that abilitates live plotting. Defaults to True.
            slurm_execution (bool): Flag that defines if the liveplot will be held through Dash or a notebook cell.
                                    Defaults to True.
            port_number (int | None): Optional parameter for when slurm_execution is True.
                                    It defines the port number of the Dash server. Defaults to None.

        Returns:
            str: The path to the file where the results are stored.

        Example:
            .. code-block:: python

                from qililab import Experiment

                # Initialize your experiment
                experiment = Experiment(label="my_experiment")
                # Add variables, loops, and operations to the experiment
                # ...

                # Execute the experiment on the platform
                results_path = platform.execute_experiment(experiment=experiment, database=False)
                print(f"Results saved to {results_path}")

        Example with database:
            .. code-block:: python

                from qililab import Experiment

                # Initialize your experiment
                experiment = Experiment(label="my_experiment")
                # Add variables, loops, and operations to the experiment
                # ...

                # Define the database manager. Optional, as this can be done inside execute_experiment
                db_manager = platform.load_db_manager(db_manager_ini_path)
                db_manager.set_sample_and_cooldown(sample=sample, cooldown=cooldown)

                # Execute the experiment on the platform
                results_path = platform.execute_experiment(experiment=experiment, database=True)
                print(f"Results saved to {results_path}")

        Note:
            - Ensure that the experiment is properly configured before execution.
            - The results will be saved in a directory within the load_db_manager config file. The default format is `{date}/{time}/{label}.h5`.
            - This method handles the setup and execution internally, providing a simplified interface for experiment execution.
        """

        if self.save_experiment_results_in_database and not self.db_manager:
            try:
                self.load_db_manager()
            except ReferenceError:
                raise ReferenceError("Missing initialization information at the desired database '.ini' path.")

        executor = ExperimentExecutor(
            platform=self,
            experiment=experiment,
            live_plot=live_plot,
            slurm_execution=slurm_execution,
            port_number=port_number,
        )
        return executor.execute()

    def compile_qprogram(
        self, qprogram: QProgram, bus_mapping: dict[str, str] | None = None, calibration: Calibration | None = None
    ) -> QbloxCompilationOutput | QuantumMachinesCompilationOutput:
        bus_aliases = {bus_mapping[bus] if bus_mapping and bus in bus_mapping else bus for bus in qprogram.buses}
        buses = [self.buses.get(alias=bus_alias) for bus_alias in bus_aliases]
        instruments = {
            instrument
            for bus in buses
            for instrument in bus.instruments
            if isinstance(instrument, (QbloxModule, QuantumMachinesCluster))
        }
        if all(isinstance(instrument, QbloxModule) for instrument in instruments):
            # Retrieve the time of flight parameter from settings
            times_of_flight = {
                bus.alias: int(bus.get_parameter(Parameter.TIME_OF_FLIGHT)) for bus in buses if bus.has_adc()
            }
            delays = {bus.alias: int(bus.get_parameter(Parameter.DELAY)) for bus in buses}
            # Determine what should be the initial value of the markers for each bus.
            # This depends on the model of the associated Qblox module and the `output` setting of the associated sequencer.
            markers = {}
            for bus in buses:
                for instrument, channel in zip(bus.instruments, bus.channels):
                    if isinstance(instrument, QbloxModule):
                        sequencer = instrument.get_sequencer(sequencer_id=channel)
                        if instrument.name == InstrumentName.QCMRF:
                            markers[bus.alias] = "".join(
                                ["1" if i in [0, 1] and i in sequencer.outputs else "0" for i in range(4)]
                            )[::-1]
                        elif instrument.name == InstrumentName.QRMRF:
                            markers[bus.alias] = "".join(
                                ["1" if i in [1] and i - 1 in sequencer.outputs else "0" for i in range(4)]
                            )[::-1]
                        else:
                            markers[bus.alias] = "0000"
            qblox_compiler = QbloxCompiler()
            return qblox_compiler.compile(
                qprogram=qprogram,
                bus_mapping=bus_mapping,
                calibration=calibration,
                times_of_flight=times_of_flight,
                delays=delays,
                markers=markers,
            )
        if all(isinstance(instrument, QuantumMachinesCluster) for instrument in instruments):
            if len(instruments) != 1:
                raise NotImplementedError(
                    "Executing QProgram in more than one Quantum Machines Cluster is not supported."
                )
            thresholds: dict[str, float] = {
                bus.alias: float(bus.get_parameter(parameter=Parameter.THRESHOLD) or 0.0)
                for bus in buses
                if bus.has_adc()
            }
            threshold_rotations: dict[str, float] = {
                bus.alias: float(bus.get_parameter(parameter=Parameter.THRESHOLD_ROTATION) or 0.0)
                for bus in buses
                if bus.has_adc()
            }

            compiler = QuantumMachinesCompiler()
            return compiler.compile(
                qprogram=qprogram,
                bus_mapping=bus_mapping,
                thresholds=thresholds,
                threshold_rotations=threshold_rotations,
                calibration=calibration,
            )
        raise NotImplementedError("Compiling QProgram for a mixture of instruments is not supported.")

    def execute_compilation_output(
        self,
        output: QbloxCompilationOutput | QuantumMachinesCompilationOutput,
        debug: bool = False,
    ):
        if isinstance(output, QbloxCompilationOutput):
            return self._execute_qblox_compilation_output(output=output, debug=debug)

        buses = [self.buses.get(alias=bus_alias) for bus_alias in output.qprogram.buses]
        instruments = {instrument for bus in buses for instrument in bus.instruments if bus.has_adc()}
        if len(instruments) != 1:
            raise NotImplementedError("Executing QProgram in more than one Quantum Machines Cluster is not supported.")
        cluster: QuantumMachinesCluster = cast("QuantumMachinesCluster", next(iter(instruments)))
        return self._execute_quantum_machines_compilation_output(output=output, cluster=cluster, debug=debug)

    def _execute_qblox_compilation_output(self, output: QbloxCompilationOutput, debug: bool = False):
        sequences, acquisitions = output.sequences, output.acquisitions
        buses = {bus_alias: self.buses.get(alias=bus_alias) for bus_alias in sequences}
        for bus_alias, bus in buses.items():
            if bus.distortions:
                for distortion in bus.distortions:
                    for waveform in sequences[bus_alias]._waveforms._waveforms:
                        sequences[bus_alias]._waveforms.modify(waveform.name, distortion.apply(waveform.data))
        if debug:
            with open("debug_qblox_execution.txt", "w", encoding="utf-8") as sourceFile:
                for bus_alias, sequence in sequences.items():
                    print(f"Bus {bus_alias}:", file=sourceFile)
                    print(str(sequence._program), file=sourceFile)
                    print(file=sourceFile)

        # Upload sequences
        for bus_alias in sequences:
            sequence_hash = hash_qpy_sequence(sequence=sequences[bus_alias])
            if bus_alias not in self._qpy_sequence_cache or self._qpy_sequence_cache[bus_alias] != sequence_hash:
                buses[bus_alias].upload_qpysequence(qpysequence=sequences[bus_alias])
                self._qpy_sequence_cache[bus_alias] = sequence_hash
            # sync all relevant sequences
            for instrument, channel in zip(buses[bus_alias].instruments, buses[bus_alias].channels):
                if isinstance(instrument, QbloxModule):
                    instrument.sync_sequencer(sequencer_id=int(channel))

        # Execute sequences
        for bus_alias in sequences:
            buses[bus_alias].run()

        # Acquire results
        results = QProgramResults()
        for bus_alias, bus in buses.items():
            if bus.has_adc():
                for instrument, channel in zip(buses[bus_alias].instruments, buses[bus_alias].channels):
                    if isinstance(instrument, QbloxModule):
                        bus_results = bus.acquire_qprogram_results(
                            acquisitions=acquisitions[bus_alias], channel_id=int(channel)
                        )
                        for bus_result in bus_results:
                            results.append_result(bus=bus_alias, result=bus_result)

        # Reset instrument settings
        for bus_alias in sequences:
            for instrument, channel in zip(buses[bus_alias].instruments, buses[bus_alias].channels):
                if isinstance(instrument, QbloxModule):
                    instrument.desync_sequencer(sequencer_id=int(channel))

        return results

    def _execute_quantum_machines_compilation_output(
        self,
        output: QuantumMachinesCompilationOutput,
        cluster: QuantumMachinesCluster,
        debug: bool = False,
    ):
        qua, configuration, measurements = output.qua, output.configuration, output.measurements
        try:
            cluster.append_configuration(configuration=configuration)

            if debug:
                with open("debug_qm_execution.py", "w", encoding="utf-8") as sourceFile:
                    print(generate_qua_script(qua, cluster.config), file=sourceFile)

            compiled_program_id = cluster.compile(program=qua)
            job = cluster.run_compiled_program(compiled_program_id=compiled_program_id)

            acquisitions = cluster.get_acquisitions(job=job)

            results = QProgramResults()
            # Doing manual classification of results as QM does not return thresholded values like Qblox
            for measurement in measurements:
                measurement_result = QuantumMachinesMeasurementResult(
                    measurement.bus,
                    *[acquisitions[handle] for handle in measurement.result_handles],
                )
                measurement_result.set_classification_threshold(measurement.threshold)
                results.append_result(bus=measurement.bus, result=measurement_result)

            return results

        except Exception as e:
            cluster.turn_off()
            raise e

        return results

    def execute_qprogram(
        self,
        qprogram: QProgram,
        bus_mapping: dict[str, str] | None = None,
        calibration: Calibration | None = None,
        debug: bool = False,
    ) -> QProgramResults:
        """Execute a :class:`.QProgram` using the platform instruments.

        |

        **The execution is done in the following steps:**

        1. Compile the QProgram.
        2. Run the compiled QProgram.
        3. Acquire the results.

        |

        **The execution can be done for (buses associated to) two different type of clusters:**

        - For ``Qblox`` modules, the compilation is done using the :class:`.QbloxCompiler`. Which compiles the :class:`.QProgram` into``Q1ASM`` for multiple sequencers based on each bus, uploads and executes the sequences, and acquires the results.
        - For ``Quantum Machines`` clusters, the compilation is done using the :class:`.QuantumMachinesCompiler`. This compiler transforms the :class:`.QProgram` into ``QUA``, the programming language of ``Quantum Machines`` hardware. It then executes the resulting ``QUA`` program and returns the results, organized by bus.

        Args:
            qprogram (QProgram): The :class:`.QProgram` to execute.
            bus_mapping (dict[str, str], optional): A dictionary mapping the buses in the :class:`.QProgram` (keys )to the buses in the platform (values).
                It is useful for mapping a generic :class:`.QProgram` to a specific experiment. Defaults to None.
            calibration (Calibration, optional): :class:`.Calibration` instance containing information of previously calibrated values, like waveforms, weights and crosstalk matrix. Defaults to None.
            debug (bool, optional): Whether to create debug information. For ``Qblox`` clusters all the program information is printed on screen.
                For ``Quantum Machines`` clusters a ``.py`` file is created containing the ``QUA`` and config compilation. Defaults to False.

        Returns:
            QProgramResults: The results of the execution. ``QProgramResults.results()`` returns a dictionary (``dict[str, list[Result]]``) of measurement results.
            The keys correspond to the buses a measurement were performed upon, and the values are the list of measurement results in chronological order.
        """
        output = self.compile_qprogram(qprogram=qprogram, bus_mapping=bus_mapping, calibration=calibration)
        return self.execute_compilation_output(output=output, debug=debug)

    def execute_qprograms_parallel(
        self,
        qprograms: list[QProgram],
        bus_mapping: dict[str, str] | None = None,
        calibration: Calibration | None = None,
        debug: bool = False,
    ) -> list[QProgramResults]:
        """Compiles a list of qprograms to be executed in parallel. Then it calls the execute_compilation_outputs_parallel method to execute the compiled qprograms.
        It loads each qprogram into a different sequencer and uses the multiplexing capabilities of QBlox to run all sequencers at the same time.

        **The execution can be done for (buses associated to) Qblox only. And it can only be done for qprograms that do not share buses.**

        Args:
            qprograms (QProgram): A list of the :class:`.QProgram` to execute.
            bus_mapping (dict[str, str], optional): A dictionary mapping the buses in the :class:`.QProgram` (keys )to the buses in the platform (values).
                It is useful for mapping a generic :class:`.QProgram` to a specific experiment. Defaults to None.
            calibration (Calibration, optional): :class:`.Calibration` instance containing information of previously calibrated values, like waveforms, weights and crosstalk matrix. Defaults to None.
            debug (bool, optional): Whether to create debug information. For ``Qblox`` clusters all the program information is printed on screen.
                Defaults to False.

        Returns:
            QProgramResults: The results of the execution. ``QProgramResults.results()`` returns a list of dictionary (``dict[str, list[Result]]``) of measurement results.
            Each element of the list corresponds to a sequencer.
            The keys correspond to the buses a measurement were performed upon, and the values are the list of measurement results in chronological order.
        """
        buses_per_qprogram = [qprogram.buses for qprogram in qprograms]
        total_buses = sum(len(s) for s in buses_per_qprogram)
        unique_buses = len(set.union(*buses_per_qprogram))
        if total_buses != unique_buses:
            raise ValueError("QPrograms cannot be executed in parallel.")
        outputs = [
            self.compile_qprogram(qprogram=qprogram, bus_mapping=bus_mapping, calibration=calibration)
            for qprogram in qprograms
        ]
        if any(isinstance(output, QuantumMachinesCompilationOutput) for output in outputs):
            raise ValueError("Parallel execution is not supported in Quantum Machines.")
        return self.execute_compilation_outputs_parallel(
            outputs=cast("list[QbloxCompilationOutput]", outputs), debug=debug
        )

    def execute_compilation_outputs_parallel(
        self,
        outputs: list[QbloxCompilationOutput],
        debug: bool = False,
    ):
        """Execute compiled qprograms in parallel.
        It loads each qprogram into a different sequencer and uses the multiplexing capabilities of QBlox to run all sequencers at the same time.

        |

        **The execution is done in the following steps:**

        1. Upload all sequences.
        2. Execute all sequences.
        3. Acquire the results.

        |

        **The execution can be done for (buses associated to) Qblox only.**

        Args:
            outputs: A list of the compiled qprograms.
            debug (bool, optional): Whether to create debug information. For ``Qblox`` clusters all the program information is printed on screen.
                Defaults to False.

        Returns:
            QProgramResults: The results of the execution. ``QProgramResults.results()`` returns a list of dictionary (``dict[str, list[Result]]``) of measurement results.
            Each element of the list corresponds to a sequencer.
            The keys correspond to the buses a measurement were performed upon, and the values are the list of measurement results in chronological order.
        """
        sequences_per_qprogram = [output.sequences for output in outputs]
        aquisitions_per_qprogram = [output.acquisitions for output in outputs]
        buses_per_qprogram = [
            {bus_alias: self.buses.get(alias=bus_alias) for bus_alias in sequences}
            for sequences in sequences_per_qprogram
        ]
        for qprogram_idx, buses in enumerate(buses_per_qprogram):
            for bus_alias, bus in buses.items():
                if bus.distortions:
                    for distortion in bus.distortions:
                        for waveform in sequences_per_qprogram[qprogram_idx][bus_alias]._waveforms._waveforms:
                            sequences_per_qprogram[qprogram_idx][bus_alias]._waveforms.modify(
                                waveform.name, distortion.apply(waveform.data)
                            )

        if debug:
            with open("debug_qblox_execution.txt", "w", encoding="utf-8") as sourceFile:
                for qprogram_idx, sequences in enumerate(sequences_per_qprogram):
                    print(f"QProgram {qprogram_idx}:", file=sourceFile)
                    for bus_alias, sequence in sequences.items():
                        print(f"Bus {bus_alias}:", file=sourceFile)
                        print(str(sequence._program), file=sourceFile)
                        print(file=sourceFile)

        # Upload sequences
        for qprogram_idx, sequences in enumerate(sequences_per_qprogram):
            for bus_alias in sequences:
                sequence_hash = hash_qpy_sequence(sequence=sequences[bus_alias])
                if bus_alias not in self._qpy_sequence_cache or self._qpy_sequence_cache[bus_alias] != sequence_hash:
                    buses_per_qprogram[qprogram_idx][bus_alias].upload_qpysequence(qpysequence=sequences[bus_alias])
                    self._qpy_sequence_cache[bus_alias] = sequence_hash
                # sync all relevant sequences
                for instrument, channel in zip(
                    buses_per_qprogram[qprogram_idx][bus_alias].instruments,
                    buses_per_qprogram[qprogram_idx][bus_alias].channels,
                ):
                    if isinstance(instrument, QbloxModule):
                        instrument.sync_sequencer(sequencer_id=int(channel))

        # Execute sequences
        for qprogram_idx, sequences in enumerate(sequences_per_qprogram):
            for bus_alias in sequences:
                buses_per_qprogram[qprogram_idx][bus_alias].run()

        # Acquire results
        results = [QProgramResults() for _ in outputs]
        for qprogram_idx, buses in enumerate(buses_per_qprogram):
            for bus_alias, bus in buses.items():
                if bus.has_adc():
                    for instrument, channel in zip(buses[bus_alias].instruments, buses[bus_alias].channels):
                        if isinstance(instrument, QbloxModule):
                            bus_results = bus.acquire_qprogram_results(
                                acquisitions=aquisitions_per_qprogram[qprogram_idx][bus_alias], channel_id=int(channel)
                            )
                            for bus_result in bus_results:
                                results[qprogram_idx].append_result(bus=bus_alias, result=bus_result)

        # Reset instrument settings
        for qprogram_idx, sequences in enumerate(sequences_per_qprogram):
            for bus_alias in sequences:
                for instrument, channel in zip(
                    buses_per_qprogram[qprogram_idx][bus_alias].instruments,
                    buses_per_qprogram[qprogram_idx][bus_alias].channels,
                ):
                    if isinstance(instrument, QbloxModule):
                        instrument.desync_sequencer(sequencer_id=int(channel))

        return results

    def execute(
        self,
        circuit: Circuit,
        nshots: int = 1000,
        transpilation_config: DigitalTranspilationConfig | None = None,
    ) -> QProgramResults:
        """Compiles and executes a circuit or a pulse schedule, using the platform instruments.

        If the ``program`` argument is a :class:`.Circuit`, it will first be translated into a :class:`.PulseSchedule` using the transpilation
        settings of the platform and the passed transpile onfiguration. Then the pulse schedules will be compiled into the assembly programs and executed.

        To compile to assembly programs, the ``platform.compile()`` method is called; check its documentation for more information.

        The transpilation is performed using the :meth:`.CircuitTranspiler.transpile_circuit()` method. Refer to the method's documentation or :ref:`Transpilation <transpilation>` for more detailed information.

        The main stages of this process are: **1.** Routing, **2.** Canceling Hermitian pairs, **3.** Translate to native gates, **4.** Correcting Drag phases, **5** Optimize Drag gates, **6.** Convert to pulse schedule.

        .. note ::

            Default steps are only: **3.**, **4.**, and **6.**, since they are always needed.

            To do Step **1.** set routing=True in transpilation_config (default behavior skips it).

            To do Steps **2.** and **5.** set optimize=True in transpilation_config (default behavior skips it)

        Args:
            program (``PulseSchedule`` | ``Circuit``): Circuit or pulse schedule to execute.
            num_avg (int): Number of hardware averages used.
            repetition_duration (int): Minimum duration of a single execution. Defaults to 200_000.
            num_bins (int, optional): Number of bins used. Defaults to 1.
            queue (Queue, optional): External queue used for asynchronous data handling. Defaults to None.
            transpilation_config (DigitalTranspilationConfig, optional): :class:`.DigitalTranspilationConfig` dataclass containing
                the configuration used during transpilation. Defaults to ``None`` (not changing any default value).
                Check the class:`.DigitalTranspilationConfig` documentation for the keys and values it can contain.

        Returns:
            Result: Result obtained from the execution. This corresponds to a numpy array that depending on the
                platform configuration may contain the following:

                - Scope acquisition is enabled: An array with dimension `(2, N)` which contain the scope data for
                    path0 (I) and path1 (Q). N corresponds to the length of the scope measured.

                - Scope acquisition disabled: An array with dimension `(#sequencers, 2, #bins)`.

        |

        Example Usage:

        .. code-block:: python

            from qibo import gates, Circuit
            from qibo.transpiler import ReverseTraversal, Sabre
            from qililab import build_platform
            from qililab.digital import DigitalTranspilationConfig

            # Create circuit:
            c = Circuit(5)
            c.add(gates.CNOT(1, 0))

            # Create platform:
            platform = build_platform(runcard="<path_to_runcard>")
            transp_config = DigitalTranspilationConfig(
                routing=True, optimize=False, router=Sabre, placer=ReverseTraversal
            )

            # Execute with automatic transpilation:
            result = platform.execute(c, num_avg=1000, transpilation_config=transp_config)
        """
        # Compile pulse schedule
        qprogram = self.compile(circuit, nshots, transpilation_config)

        results = self.execute_qprogram(qprogram)

        return results

    def compile(
        self,
        circuit: Circuit,
        nshots: int,
        transpilation_config: DigitalTranspilationConfig | None = None,
    ) -> QProgram:
        """Compiles the circuit / pulse schedule into a set of assembly programs, to be uploaded into the awg buses.

        If the ``program`` argument is a :class:`.Circuit`, it will first be translated into a :class:`.PulseSchedule` using the transpilation
        settings of the platform and passed  transpile configuration. Then the pulse schedules will be compiled into the assembly programs.

        .. note::

            Compile is called during ``platform.execute()``, check its documentation for more information.

        The transpilation is performed using the :meth:`.CircuitTranspiler.transpile_circuit()` method. Refer to the method's documentation or :ref:`Transpilation <transpilation>` for more detailed information.

        The main stages of this process are: **1.** Routing, **2.** Canceling Hermitian pairs, **3.** Translate to native gates, **4.** Correcting Drag phases, **5** Optimize Drag gates, **6.** Convert to pulse schedule.

        .. note ::

            Default steps are only: **3.**, **4.**, and **6.**, since they are always needed.

            To do Step **1.** set routing=True in transpilation_config (default behavior skips it).

            To do Steps **2.** and **5.** set optimize=True in transpilation_config (default behavior skips it)

        Args:
            program (PulseSchedule | Circuit): Circuit or pulse schedule to compile.
            num_avg (int): Number of hardware averages used.
            repetition_duration (int): Minimum duration of a single execution.
            num_bins (int): Number of bins used.
            transpilation_config (DigitalTranspilationConfig, optional): :class:`.DigitalTranspilationConfig` dataclass containing
                the configuration used during transpilation. Defaults to ``None`` (not changing any default value).
                Check the class:`.DigitalTranspilationConfig` documentation for the keys and values it can contain.

        Returns:
            tuple[dict, list[int] | None]: Tuple containing the dictionary of compiled assembly programs (The key is the bus alias (``str``),
                and the value is the assembly compilation (``list``)), and its corresponding final layout (Initial Re-mapping + SWAPs routing) of
                the Original Logical Qubits (l_q) in the physical circuit (wires): [l_q in wire 0, l_q in wire 1, ...] (None = trivial mapping).

        Raises:
            ValueError: raises value error if the circuit execution time is longer than ``repetition_duration`` for some qubit.
        """
        # We have a circular import because Platform uses CircuitToPulses and vice versa
        if self.digital_compilation_settings is None:
            raise ValueError("Cannot compile Circuit without gates settings.")

        physical_nqubits = max(max(pair) for pair in self.digital_compilation_settings.topology) + 1
        topology = PyGraph()
        topology.add_nodes_from(range(physical_nqubits))
        for a, b in self.digital_compilation_settings.topology:
            topology.add_edge(a, b, None)

        transpiler = CircuitTranspiler(topology)
        circuit = transpiler.run(circuit)

        compiler = CircuitToQProgramCompiler()
        qprogram = compiler.compile(circuit)

        return qprogram

    def calibrate_mixers(self, alias: str, cal_type: str, channel_id: ChannelID | None = None):
        bus = self.get_element(alias=alias)
        for instrument, instrument_channel in zip(bus.instruments, bus.channels):
            if instrument.name == InstrumentName.QRMRF:
                if channel_id is not None and channel_id == instrument_channel:
                    instrument.calibrate_mixers(cal_type, instrument_channel)
            elif instrument.name == InstrumentName.QCMRF:
                if channel_id is not None and channel_id == instrument_channel:
                    instrument.calibrate_mixers(cal_type, channel_id)
            else:
                raise AttributeError("Mixers calibration not implemented for this instrument.")

    def draw(
        self,
        qprogram: QProgram,
        time_window: int | None = None,
        averages_displayed: bool = False,
        acquisition_showing: bool = True,
        bus_mapping: dict[str, str] | None = None,
        calibration: Calibration | None = None,
    ):
        """Draw the QProgram using QBlox Compiler whilst adding the knowledge of the platform

        Args:
            time_window (int): Allows the user to stop the plotting after the specified number of ns have been plotted. The plotting might not be the precise number of ns inputted.
                For example, if the timeout is 100 ns but there is a play operation of 150 ns, the plot will display the data until 150 ns. Defaults to None.
            averages_displayed (bool): False means that all loops on the sequencer starting with avg will only loop once, and True shows all iterations. Defaults to False.
            acquisition_showing (bool): Allows visualing the acquisition period on the plot. Defaults to True.
            bus_mapping (dict[str, str], optional): A dictionary mapping the buses in the :class:`.QProgram` (keys )to the buses in the platform (values).
                It is useful for mapping a generic :class:`.QProgram` to a specific experiment. Defaults to None.

        Returns:
            plotly object: plotly.graph_objs._figure.Figure
        """
        runcard_data = self._data_draw()
        qblox_draw = QbloxDraw()
        sequencer = self.compile_qprogram(qprogram, bus_mapping, calibration)
        plotly_figure, _ = qblox_draw.draw(
            sequencer, runcard_data, time_window, averages_displayed, acquisition_showing
        )

        return plotly_figure

    def load_db_manager(self, db_ini_path: str | None = None):
        """Load Database Manager from an .ini path containing user DB user information or if no path is given
        it uses '~/database.ini'.

        Args:
            db_ini_path (str | None, optional): Database manager initialization file path. Defaults to None.

        Returns:
            DatabaseManager: Database manager class
        """
        if db_ini_path:
            self.db_manager = get_db_manager(db_ini_path)
        else:
            self.db_manager = get_db_manager()
        return self.db_manager

    def db_real_time_saving(
        self,
        shape: tuple,
        loops: dict[str, np.ndarray],
        experiment_name: str,
        qprogram: QProgram | None = None,
        description: str | None = None,
    ):
        """Allows for real time saving of results from an experiment.

        This class wraps a numpy array and adds a context manager to save results and database metadata on real time
        while they are acquired by the instruments.

        Example usage of this function:

            .. code-block:: python

                platform = ql.build_platform(runcard=runcard)
                platform.connect()
                platform.initial_setup()
                platform.turn_on_instruments()

                db_manager = platform.load_db_manager(db_manager_ini_path)
                db_manager.set_sample_and_cooldown(sample=sample, cooldown=cooldown)

                (experiment definition)

                stream_array = platform.database_saving(
                    shape=(len(if_sweep), 2),
                    loops={"frequency": if_sweep},
                    experiment_name="resonator_spectroscopy",
                    qprogram=qprogram,
                    description="optional text"
                )

                with stream_array:
                    results = platform.execute_qprogram(qprogram).results
                    stream_array[()] = results[readout_bus][0].array.T


        Args:
            shape (tuple): results array shape.
            loops (dict[str, np.ndarray]): Dictionary of loops with the name of the loop and the array.
            experiment_name (str): Name of the experiment.
            qprogram (QProgram | None, optional): Qprogram of the experiment, if there is no Qprogram related to the results it is not mandatory. Defaults to None.
            description (str | None, optional): String containing a description or any rellevant information about the experiment. Defaults to None.

        Returns:
            StreamArray: StreamArray class to process and save the data
        """

        if not self.db_manager:
            raise ReferenceError("Missing db_manager, try using platform.load_db_manager().")

        return StreamArray(
            shape=shape,
            loops=loops,
            platform=self,
            qprogram=qprogram,
            experiment_name=experiment_name,
            db_manager=self.db_manager,
            optional_identifier=description,
        )

    def db_save_results(
        self,
        experiment_name: str,
        results: np.ndarray,
        loops: dict[str, np.ndarray] | dict[str, dict[str, Any]],
        qprogram: QProgram | None = None,
        description: str | None = None,
    ):
        """Uses the same StreamArray class as for live saving but it saves full chunks of data in the same format as platform.stream_array.

        Example usage of this function:

            .. code-block:: python

                platform = ql.build_platform(runcard=runcard)
                platform.connect()
                platform.initial_setup()
                platform.turn_on_instruments()

                db_manager = platform.load_db_manager(db_manager_ini_path)
                db_manager.set_sample_and_cooldown(sample=sample, cooldown=cooldown)

                results = Create experiment results without live saving, either not needed or incapable (VNA data)
                or
                results = old results to be saved inside the database

                saving_path = platform.save_measurement_results(
                    experiment_name="resonator_spectroscopy",
                    results = results
                    loops={"frequency": if_sweep},
                    qprogram=qprogram,
                    description="optional text"
                )

        Args:
            experiment_name (str): Name of the experiment.
            results (np.ndarray): Experiment data.
            loops (dict[str, np.ndarray]): Dictionary of loops with the name of the loop and the array.
            qprogram (QProgram | None, optional): Qprogram of the experiment, if there is no Qprogram related to the results it is not mandatory. Defaults to None.
            description (str | None, optional): String containing a description or any rellevant information about the experiment. Defaults to None.
        """

        if not self.db_manager:
            raise ReferenceError("Missing db_manager, try using platform.load_db_manager().")

        shape = results.shape

        if len(loops) != len(shape) - 1:
            raise ValueError(
                "Number of loops must be the same as the number of dimensions of the results except for IQ"
            )

        for iteration, (loop_name, loop_array) in enumerate(loops.items()):
            if isinstance(loop_array, dict):
                loop_array = loop_array["array"]
            if loop_array.shape[0] != shape[iteration] - 1:  # type: ignore
                raise ValueError(
                    f"Loops dimensions must be the same than the array instroduced, {loop_name} as {loop_array.shape[0]} != {shape[iteration]}"  # type: ignore
                )

        stream_array = StreamArray(
            shape=shape,
            loops=loops,
            platform=self,
            qprogram=qprogram,
            experiment_name=experiment_name,
            db_manager=self.db_manager,
            optional_identifier=description,
        )

        with stream_array:
            for index in range(shape[0]):
                stream_array[index,] = results[index, ...]  # type: ignore
        return stream_array.path
