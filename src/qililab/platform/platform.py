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
import warnings
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Callable, cast

import numpy as np
from ruamel.yaml import YAML

from qililab.analog import AnnealingProgram
from qililab.config import logger
from qililab.constants import FLUX_CONTROL_REGEX, GATE_ALIAS_REGEX, RUNCARD
from qililab.core.variables import Domain
from qililab.digital import CircuitToQProgramCompiler, CircuitTranspiler, qprogram_results_to_samples
from qililab.exceptions import ExceptionGroup
from qililab.extra.quantum_machines import (
    QuantumMachinesCluster,
    QuantumMachinesCompilationOutput,
    QuantumMachinesCompiler,
    QuantumMachinesMeasurementResult,
    generate_qua_script,
)
from qililab.instrument_controllers import InstrumentController, InstrumentControllers
from qililab.instrument_controllers.qblox import QbloxClusterController
from qililab.instrument_controllers.utils import InstrumentControllerFactory
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.instruments.qblox import QbloxModule
from qililab.instruments.qblox.qblox_draw import QbloxDraw
from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2
from qililab.instruments.utils import InstrumentFactory
from qililab.platform.components.bus import Bus
from qililab.platform.components.buses import Buses
from qililab.qililab_settings import get_settings
from qililab.qprogram import (
    Calibration,
    Experiment,
    QbloxCompilationOutput,
    QbloxCompiler,
    QProgram,
    QProgramCompilationOutput,
)
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix, FluxVector
from qililab.qprogram.experiment_executor import ExperimentExecutor
from qililab.qprogram.qdac_compiler import QdacCompiler
from qililab.result.database import get_db_manager
from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult
from qililab.result.qprogram.qprogram_results import QProgramResults
from qililab.result.stream_results import StreamArray
from qililab.typings import ChannelID, DistortionState, InstrumentName, OutputID, Parameter, ParameterValue
from qililab.utils import hash_qpy_sequence

if TYPE_CHECKING:
    import numpy as np
    from qilisdk.digital import Circuit

    from qililab.instrument_controllers.instrument_controller import InstrumentController
    from qililab.instruments.instrument import Instrument
    from qililab.result.database import DatabaseManager
    from qililab.settings import Runcard


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

    After initializing a Platform, the typical first three steps (which are usually only required at the start) are:

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

        You could also get the results in a more standard format, as already classified ``counts`` or ``probabilities`` dictionaries.
        To do so the call to execute circuit must be slightly different, as the number of averages must be 1:

        .. code-block:: python

            # Executing the platform with the same amount of loops but using bins:
            result = platform.execute(program=circuit, num_avg=1, num_bins=1000, repetition_duration=6000)

        Then:

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

        If you print the results, you'll see how you obtain the sinusoidal expected behavior!

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

        self.crosstalk: CrosstalkMatrix | None = None
        """Crosstalk matrix information, defaults to None (only used on FLUX parameters)"""

        self.flux_vector: FluxVector | None = None
        """Flux vector information, defaults to None (only used on FLUX parameters)"""

        self.flux_parameter: dict[str, int | float | bool | str] = {}
        """Flux dictionary with information for the get parameter (only used on FLUX parameters)"""

        self.db_manager: DatabaseManager | None = None
        """Database manager for experiment class and db stream array"""

        self.trigger_runs: int = 0

        self.qblox_alias_module: list = self._get_qblox_alias_module()
        """List of dict with key the alias of qblox module and value the module_id. Used for the qblox distortions"""

        self.qblox_active_filter_exponential: list = self._get_qblox_active_filter_exponential()
        """List of exponential_idx with an active exponential filter. Active is considered as either "enabled" or "delay_comp". Used for the qblox distortions"""

        self.qblox_active_filter_fir: bool = self._get_qblox_active_filter_fir()
        """Bool to determine if any FIR filter is active. Active is considered as either "enabled" or "delay_comp". Used for the qblox distortions"""

        self._update_qblox_filter_state_exponential()
        """Updates the exponential state as needed. Used for the qblox distortions"""

        self._update_qblox_filter_state_fir()
        """Updates the FIR state as needed. Used for the qblox distortions"""

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

    def get_parameter(
        self, alias: str, parameter: Parameter, channel_id: ChannelID | None = None, output_id: OutputID | None = None
    ):
        """Get platform parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            alias (str): Alias of the bus where the parameter is set.
            channel_id (int, optional): ID of the channel we want to use to set the parameter. Defaults to None.
            output_id (int, optional): ID of the module we want to use to set the parameter, used for Qblox distortion filters. Defaults to None.
        """
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        if alias == "platform" or regex_match is not None:
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
        return element.get_parameter(parameter=parameter, channel_id=channel_id, output_id=output_id)

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
                                            dac_offset_i = bus.get_parameter(Parameter.OUT0_OFFSET_PATH0) / 1000
                                            dac_offset_q = bus.get_parameter(Parameter.OUT0_OFFSET_PATH1) / 1000
                                        elif out == 1:
                                            dac_offset_i = bus.get_parameter(Parameter.OUT1_OFFSET_PATH0) / 1000
                                            dac_offset_q = bus.get_parameter(Parameter.OUT1_OFFSET_PATH1) / 1000

                            data_oscilloscope[bus.alias]["dac_offset_i"] = dac_offset_i
                            data_oscilloscope[bus.alias]["dac_offset_q"] = dac_offset_q

        else:
            # TODO: the same information could be generated with a Quantum Machine runcard, even if the QBlox Compiler is used in the background.
            raise NotImplementedError("The drawing feature is currently only supported for QBlox.")

        return data_oscilloscope

    def _get_qblox_active_filter_fir(self):
        """Determines if any FIR filter is active. Active is considered as either "enabled" or "delay_comp"

        Returns:
            qblox_active_filter(bool): true if any FIR filter is active, False otherwise. Defaults to False
        """
        qblox_active_filter = False
        for pair in self.qblox_alias_module:
            module_alias, output_id = next(iter(pair.items()))
            qblox_instrument = self.instruments.get_instrument(module_alias)
            for filter in qblox_instrument.filters:
                if filter.output_id == output_id:
                    if filter.fir_state in {DistortionState.ENABLED, DistortionState.DELAY_COMP}:
                        qblox_active_filter = True
        return qblox_active_filter

    def _get_qblox_active_filter_exponential(self):
        """Determines which exponential index has an active exponential filter. Active is considered as either "enabled" or "delay_comp"

        Returns:
            qblox_active_filter(list): List index of exponential for which an exponential filter is active.
        """
        qblox_active_filter = []
        for pair in self.qblox_alias_module:
            module_alias, output_id = next(iter(pair.items()))
            qblox_instrument = self.instruments.get_instrument(module_alias)
            for filter in qblox_instrument.filters:
                if filter.output_id == output_id:
                    if filter.exponential_state is not None:
                        for idx, state_exponential in enumerate(filter.exponential_state):
                            if (
                                state_exponential in {DistortionState.ENABLED, DistortionState.DELAY_COMP}
                                and idx not in qblox_active_filter
                            ):
                                qblox_active_filter.append(idx)
        return qblox_active_filter

    def _get_qblox_alias_module(self):
        """Maps the qblox alias to the module_id defined in the bus mapping of the runcard

        Returns:
            qblox_alias_module(list): List of dict with key the alias of qblox module and value the module_id
        """
        buses = list(self.buses)
        qblox_alias_module = []
        for bus in buses:
            for instrument, channel in zip(bus.instruments, bus.channels):
                if isinstance(instrument, QbloxModule):
                    output_channels = instrument.awg_sequencers[channel].outputs
                    for output_channel in output_channels:
                        pair = {instrument.alias: output_channel}
                        if pair not in qblox_alias_module:
                            qblox_alias_module.append(pair)
        return qblox_alias_module

    def set_parameter(
        self,
        alias: str,
        parameter: Parameter,
        value: ParameterValue,
        channel_id: ChannelID | None = None,
        output_id: OutputID | None = None,
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
            output_id (int, optional): ID of the module we want to use to set the parameter, used for Qblox distortion filters. Defaults to None.
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

        if parameter in {
            Parameter.EXPONENTIAL_STATE_0,
            Parameter.EXPONENTIAL_STATE_1,
            Parameter.EXPONENTIAL_STATE_2,
            Parameter.EXPONENTIAL_STATE_3,
        }:
            exponential_idx = int(parameter.value[-1])
            if value is True:
                if exponential_idx not in self.qblox_active_filter_exponential:
                    self.qblox_active_filter_exponential.append(exponential_idx)
                self._update_qblox_filter_state_exponential()
            else:
                if (
                    exponential_idx in self.qblox_active_filter_exponential
                ):  # cannot put the filter as bypassed otherwise this would cause a delay with the other sequencers
                    element.set_parameter(
                        parameter=parameter,
                        value=DistortionState.DELAY_COMP,
                        channel_id=channel_id,
                        output_id=output_id,
                    )
                    if value in {DistortionState.BYPASSED, False}:
                        logger.warning(
                            "Another exponential filter is marked as active hence it is not possible to disable this filter otherwise this would cause a delay with the other sequencers."
                        )
                    return

        if parameter == Parameter.FIR_STATE:
            if value is True:
                self.qblox_active_filter_fir = True
                self._update_qblox_filter_state_fir()

            elif (
                self.qblox_active_filter_fir
            ):  # cannot put the filter as bypassed otherwise this would cause a delay with the other sequencers
                element.set_parameter(
                    parameter=parameter, value=DistortionState.DELAY_COMP, channel_id=channel_id, output_id=output_id
                )
                if value in {DistortionState.BYPASSED, False}:
                    logger.warning(
                        "Another FIR filter is marked as active hence it is not possible to disable this filter otherwise this would cause a delay with the other sequencers."
                    )
                return
        element.set_parameter(parameter=parameter, value=value, channel_id=channel_id, output_id=output_id)

    def _update_qblox_filter_state_exponential(self):
        """Updates the exponential state as needed.
        If any exponential idx is active ("enabled" or "delay_comp"), the exponential state of all other outputs will be updated to "delay_comp".
        This ensures that there are no delays between outputs that have a filter "enabled" or "delay_comp" and outputs with bypassed filters.
        """
        if self.qblox_active_filter_exponential:
            for pair in self.qblox_alias_module:
                alias, output_id = next(iter(pair.items()))
                for expo_idx in self.qblox_active_filter_exponential:
                    parameter = getattr(Parameter, f"EXPONENTIAL_STATE_{expo_idx}")
                    pre_exisisting_filter = False
                    qblox_instrument = self.get_element(alias=alias)
                    for filter in qblox_instrument.filters:
                        if (
                            filter.output_id == output_id
                            and pre_exisisting_filter is False
                            and filter.exponential_state is not None
                        ):
                            if len(filter.exponential_state) > expo_idx:
                                pre_exisisting_filter = True
                                state_exponential = self.get_parameter(
                                    alias=alias, parameter=parameter, output_id=output_id
                                )
                                if state_exponential not in {DistortionState.ENABLED, DistortionState.DELAY_COMP}:
                                    self.set_parameter(
                                        alias=alias,
                                        parameter=parameter,
                                        value=DistortionState.DELAY_COMP,
                                        output_id=output_id,
                                    )
                    if pre_exisisting_filter is False:  # filter needs to be created
                        self.set_parameter(
                            alias=alias, parameter=parameter, value=DistortionState.DELAY_COMP, output_id=output_id
                        )

    def _update_qblox_filter_state_fir(self):
        """Updates the FIR state as needed.
        If any FIR filter is active ("enabled" or "delay_comp"), the FIR state of all other outputs will be updated to "delay_comp".
        This ensures that there are no delays between outputs that have a filter "enabled" or "delay_comp" and outputs with bypassed filters.
        """
        if self.qblox_active_filter_fir:
            for pair in self.qblox_alias_module:
                alias, output_id = next(iter(pair.items()))
                pre_exisisting_filter = False
                qblox_instrument = self.get_element(alias=alias)
                for filter in qblox_instrument.filters:
                    if (
                        filter.output_id == output_id
                        and pre_exisisting_filter is False
                        and filter.fir_state is not None
                    ):
                        pre_exisisting_filter = True
                        state_fir = self.get_parameter(alias=alias, parameter=Parameter.FIR_STATE, output_id=output_id)
                        if state_fir not in {DistortionState.ENABLED, DistortionState.DELAY_COMP}:
                            self.set_parameter(
                                alias=alias,
                                parameter=Parameter.FIR_STATE,
                                value=DistortionState.DELAY_COMP,
                                output_id=output_id,
                            )
                if pre_exisisting_filter is False:  # filter needs to be created
                    self.set_parameter(
                        alias=alias,
                        parameter=Parameter.FIR_STATE,
                        value=DistortionState.DELAY_COMP,
                        output_id=output_id,
                    )

    def _set_bias_from_element(self, element: Bus | InstrumentController | Instrument | None):  # type: ignore[union-attr]
        """Sets the right parameter depending on the instrument defined inside the element.
        This is used in the crosstalk correction.
        The instruments included in this function are: QM, QBlox, SPI and QDevil.

        Args:
            element (_type_): runcard element.

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

        if not self.crosstalk:
            raise ValueError("Crosstalk matrix has not been set")

        if not bus_list:
            bus_list = list(self.crosstalk.matrix.keys())

        if not self.flux_vector:
            self.flux_vector = FluxVector()
        for flux in bus_list:
            if flux not in self.flux_vector.flux_vector.keys():
                self.flux_vector[flux] = 0
            self.flux_vector.bias_vector[flux] = 0
            self.flux_vector.set_crosstalk_from_bias(self.crosstalk)

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
                self.digital_compilation_settings.model_dump()
                if self.digital_compilation_settings is not None
                else None
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
        execution_error: Exception | None = None
        try:
            # Track successfully called setup methods and their cleanup counterparts
            self.connect()
            cleanup_methods.append(self.disconnect)  # Store disconnect for cleanup

            self.initial_setup()  # No specific cleanup for initial_setup

            self.turn_on_instruments()
            cleanup_methods.append(self.turn_off_instruments)  # Store turn_off_instruments for cleanup

            yield  # Experiment logic goes here

        except Exception as e:  # noqa: BLE001
            logger.error(f"An error occurred: {e}")
            execution_error = e
        finally:
            # Call the cleanup methods in reverse order
            for cleanup_method in reversed(cleanup_methods):
                try:
                    cleanup_method()
                except Exception as cleanup_exception:  # noqa: BLE001
                    logger.error(f"Error during cleanup: {cleanup_exception}")
                    cleanup_errors.append(cleanup_exception)

            # Raise any exception that might have happened during cleanup
            if cleanup_errors:
                if execution_error is not None:
                    raise ExceptionGroup(
                        "Exceptions occurred during execution and cleanup",
                        [execution_error, *cleanup_errors],
                    )
                if len(cleanup_errors) == 1:
                    raise cleanup_errors[0]
                raise ExceptionGroup("Exceptions occurred during cleanup", cleanup_errors)

            if execution_error is not None:
                raise execution_error

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
        The annealing program should contain a time ordered list of circuit elements and their corresponding ising coefficients as a dictionary. Example structure:

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

        This dictionary containing ising coefficients is transpiled to fluxes using the given transpiler. Then the corresponding waveforms are obtained and assigned to a bus
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
        job_id: int | None = None,
        sample: str | None = None,
        cooldown: str | None = None,
    ) -> str:
        """Executes a quantum experiment on the platform.

        This method manages the execution of a given `Experiment` on the platform by utilizing an `ExperimentExecutor`. It orchestrates the entire process, including traversing the experiment's structure, handling loops and operations, and streaming results in real-time to ensure data integrity. Result storage paths, live plotting, and database persistence are configured through :func:`qililab.qililab_settings.get_settings`.

        Args:
            experiment (Experiment): The experiment object defining the sequence of operations and loops.

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
                results_path = platform.execute_experiment(experiment=experiment)
                print(f"Results saved to {results_path}")

        Example with database:
            .. code-block:: python

                from qililab import Experiment, get_settings

                # Initialize your experiment
                experiment = Experiment(label="my_experiment")
                # Add variables, loops, and operations to the experiment
                # ...

                # Define the database manager. Optional, as this can be done inside execute_experiment
                db_manager = platform.load_db_manager(db_manager_ini_path)
                db_manager.set_sample_and_cooldown(sample=sample, cooldown=cooldown)

                settings = get_settings()
                settings.experiment_results_save_in_database = True

                # Execute the experiment on the platform
                results_path = platform.execute_experiment(experiment=experiment)
                print(f"Results saved to {results_path}")

        Note:
            - Ensure that the experiment is properly configured before execution.
            - The results will be saved in a directory within the load_db_manager config file. The default format is `{date}/{time}/{label}.h5`.
            - This method handles the setup and execution internally, providing a simplified interface for experiment execution.
        """

        if get_settings().experiment_results_save_in_database and not self.db_manager:
            try:
                self.load_db_manager()
            except ReferenceError:
                raise ReferenceError("Missing initialization information at the desired database '.ini' path.")

        executor = ExperimentExecutor(
            platform=self,
            experiment=experiment,
            job_id=job_id,
            sample=sample,
            cooldown=cooldown,
        )
        return executor.execute()

    def compile_qprogram(
        self, qprogram: QProgram, bus_mapping: dict[str, str] | None = None, calibration: Calibration | None = None
    ) -> QProgramCompilationOutput:
        bus_aliases = {bus_mapping[bus] if bus_mapping and bus in bus_mapping else bus for bus in qprogram.buses}
        buses = [self.buses.get(alias=bus_alias) for bus_alias in bus_aliases]
        instruments = {
            instrument
            for bus in buses
            for instrument in bus.instruments
            if isinstance(instrument, (QbloxModule, QuantumMachinesCluster))
        }
        qdac_buses = [
            bus for bus in buses if any(isinstance(instrument, QDevilQDac2) for instrument in bus.instruments)
        ]
        if all(isinstance(instrument, QbloxModule) for instrument in instruments):
            # Retrieve the time of flight parameter from settings
            instrument_controllers = [
                controller
                for controller in self.instrument_controllers.elements
                if isinstance(controller, QbloxClusterController)
            ]
            ext_trigger = any(controller.ext_trigger for controller in instrument_controllers)
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

            compiled_qdac = None
            if qdac_buses:
                qdac_instrument = next(
                    instrument for instrument in qdac_buses[0].instruments if isinstance(instrument, QDevilQDac2)
                )
                qdac_compiler = QdacCompiler()
                compiled_qdac = qdac_compiler.compile(
                    qprogram=qprogram,
                    qdac=qdac_instrument,
                    qdac_buses=qdac_buses,
                    bus_mapping=bus_mapping,
                    calibration=calibration,
                )

            qblox_compiler = QbloxCompiler()
            qblox_buses = [
                bus.alias for bus in buses if any(isinstance(instrument, QbloxModule) for instrument in bus.instruments)
            ]

            return QProgramCompilationOutput(
                qblox=qblox_compiler.compile(
                    qprogram=qprogram,
                    bus_mapping=bus_mapping,
                    calibration=calibration,
                    times_of_flight=times_of_flight,
                    delays=delays,
                    markers=markers,
                    ext_trigger=ext_trigger,
                    qblox_buses=qblox_buses,
                ),
                qdac=compiled_qdac,
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

            compiled_qdac = None
            if qdac_buses:
                qdac_instrument = next(
                    instrument for instrument in qdac_buses[0].instruments if isinstance(instrument, QDevilQDac2)
                )
                qdac_compiler = QdacCompiler()
                compiled_qdac = qdac_compiler.compile(
                    qprogram=qprogram,
                    qdac=qdac_instrument,
                    qdac_buses=qdac_buses,
                    bus_mapping=bus_mapping,
                    calibration=calibration,
                )

            compiler = QuantumMachinesCompiler()
            qm_buses = [
                bus
                for bus in buses
                if any(isinstance(instrument, QuantumMachinesCluster) for instrument in bus.instruments)
            ]
            return QProgramCompilationOutput(
                quantum_machines=compiler.compile(
                    qprogram=qprogram,
                    bus_mapping=bus_mapping,
                    thresholds=thresholds,
                    threshold_rotations=threshold_rotations,
                    calibration=calibration,
                    qm_buses=qm_buses,
                ),
                qdac=compiled_qdac,
            )
        raise NotImplementedError("Compiling QProgram for a mixture of AWG instruments is not supported.")

    def execute_compilation_output(
        self,
        output: QProgramCompilationOutput,
        debug: bool = False,
    ):
        if isinstance(output.qblox, QbloxCompilationOutput):
            self.trigger_runs = 0
            return self._execute_qblox_compilation_output(output=output, debug=debug)

        buses = [self.buses.get(alias=bus_alias) for bus_alias in output.quantum_machines.qprogram.buses]  # type: ignore[union-attr]
        instruments = {instrument for bus in buses for instrument in bus.instruments if bus.has_adc()}
        if len(instruments) != 1:
            raise NotImplementedError("Executing QProgram in more than one Quantum Machines Cluster is not supported.")
        cluster: QuantumMachinesCluster = cast("QuantumMachinesCluster", next(iter(instruments)))
        return self._execute_quantum_machines_compilation_output(output=output, cluster=cluster, debug=debug)

    def _execute_qblox_compilation_output(self, output: QProgramCompilationOutput, debug: bool = False):
        try:
            sequences, acquisitions = output.qblox.sequences, output.qblox.acquisitions  # type: ignore[union-attr]
            buses = {bus_alias: self.buses.get(alias=bus_alias) for bus_alias in sequences}

            for bus_alias, bus in buses.items():
                # set up the trigger network if required
                if bus_alias in output.qblox.qprogram.qblox.trigger_network_required:  # type: ignore[union-attr]
                    trigger_address = output.qblox.qprogram.qblox.trigger_network_required[bus_alias]  # type: ignore[union-attr]
                    buses[bus_alias]._setup_trigger_network(trigger_address=trigger_address)
                    for controller in self.instrument_controllers.elements:
                        if isinstance(controller, QbloxClusterController):
                            controller.device.reset_trigger_monitor_count(address=trigger_address)
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
            if output.qdac:
                if output.qdac.trigger_position == "front":
                    output.qdac.qdac.start()
                for bus_alias in sequences:
                    buses[bus_alias].run()
                if output.qdac.trigger_position == "back":
                    output.qdac.qdac.start()
            else:
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
                                for _, acquisition_data in acquisitions[bus_alias].items():
                                    intertwined = acquisition_data.intertwined
                                    unintertwined_results = self._unintertwined_qblox_results(bus_result, intertwined)
                                    for unintertwined_result in unintertwined_results:
                                        results.append_result(bus=bus_alias, result=unintertwined_result)

            # Reset instrument settings
            for bus_alias in sequences:
                for instrument, channel in zip(buses[bus_alias].instruments, buses[bus_alias].channels):
                    if isinstance(instrument, QbloxModule):
                        instrument.desync_sequencer(sequencer_id=int(channel))

            return results
        except TimeoutError as timeout:
            if output.qdac:
                warnings.warn("Timeout reached for triggered measurement, trying again.")

                # Reset instrument settings
                for bus_alias in sequences:
                    for instrument, channel in zip(buses[bus_alias].instruments, buses[bus_alias].channels):
                        if isinstance(instrument, QbloxModule):
                            instrument.desync_sequencer(sequencer_id=int(channel))
                self.trigger_runs += 1

                if self.trigger_runs <= 3:
                    return self._execute_qblox_compilation_output(output, debug)

            raise timeout

    def _unintertwined_qblox_results(
        self, bus_result: QbloxMeasurementResult, intertwined: int
    ) -> list[QbloxMeasurementResult]:
        """Return a list of results where intertwined acquisitions are separated.

        In Qililab, when multiple acquisitions or measurements are performed at the same nested level, their results are intertwined: the bins are looped over
        while the acquisition index remains constant.
        If `intertwined` is greater than 1, this function separates each acquisition into its own QbloxMeasurementResult object.
        QbloxMeasurementResult object. If `intertwined` is 1 the result is returned inside a single-element list.

        Returns:
            list[QbloxMeasurementResult]: unintertwined results where each element corresponds to one acquisition.
        """
        results_unintertwined_list = []
        if intertwined > 1:
            for result in range(intertwined):
                bus = bus_result.bus
                new_raw_measurement_data = {
                    "scope": {
                        "path0": {
                            "data": bus_result.raw_measurement_data["scope"]["path0"]["data"][result::intertwined]
                        },
                        "path1": {
                            "data": bus_result.raw_measurement_data["scope"]["path1"]["data"][result::intertwined]
                        },
                    },
                    "bins": {
                        "integration": {
                            "path0": bus_result.raw_measurement_data["bins"]["integration"]["path0"][
                                result::intertwined
                            ],
                            "path1": bus_result.raw_measurement_data["bins"]["integration"]["path1"][
                                result::intertwined
                            ],
                        },
                        "threshold": bus_result.raw_measurement_data["bins"]["threshold"][result::intertwined],
                        "avg_cnt": bus_result.raw_measurement_data["bins"]["avg_cnt"][result::intertwined],
                    },
                }
                results_unintertwined = QbloxMeasurementResult(
                    bus=bus, raw_measurement_data=new_raw_measurement_data, shape=bus_result.shape
                )
                results_unintertwined_list.append(results_unintertwined)

        else:
            results_unintertwined_list = [bus_result]

        return results_unintertwined_list

    def _execute_quantum_machines_compilation_output(
        self,
        output: QProgramCompilationOutput,
        cluster: QuantumMachinesCluster,
        debug: bool = False,
    ):
        qua = output.quantum_machines.qua  # type: ignore[union-attr]
        configuration = output.quantum_machines.configuration  # type: ignore[union-attr]
        measurements = output.quantum_machines.measurements  # type: ignore[union-attr]
        try:
            cluster.append_configuration(configuration=configuration)

            if debug:
                with open("debug_qm_execution.py", "w", encoding="utf-8") as sourceFile:
                    print(generate_qua_script(qua, cluster.config), file=sourceFile)

            compiled_program_id = cluster.compile(program=qua)

            if output.qdac:
                if output.qdac.trigger_position == "front":
                    output.qdac.qdac.start()

                job = cluster.run_compiled_program(compiled_program_id=compiled_program_id)

            else:
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

    def _normalize_bus_mappings(
        self,
        bus_mappings: list[dict[str, str] | None] | dict[str, str] | None,
        n: int,
    ) -> list[dict[str, str] | None]:
        """
        Return a list of length n with one mapping per qprogram.
        Accepts:
        - None                          -> [None] * n
        - single dict                   -> [that dict] * n
        - sequence of dict/None, len n  -> as-is
        """
        if bus_mappings is None:
            return [None] * n

        if isinstance(bus_mappings, dict):
            return [bus_mappings.copy() for _ in range(n)]

        # sequence case
        if len(bus_mappings) != n:
            raise ValueError(f"len(bus_mappings)={len(bus_mappings)} != len(qprograms)={n}")

        return bus_mappings

    def _normalize_calibrations(
        self,
        calibrations: list[Calibration | None] | Calibration | None,
        n: int,
    ) -> list[Calibration | None]:
        """
        Return a list of length n with one mapping per qprogram.
        Accepts:
        - None                          -> [None] * n
        - single Calibration instance   -> [that Calibration] * n
        - sequence of Calibration/None, len n  -> as-is
        """
        if calibrations is None:
            return [None] * n

        if isinstance(calibrations, Calibration):
            return [calibrations for _ in range(n)]

        # sequence case
        if len(calibrations) != n:
            raise ValueError(f"len(calibrations)={len(calibrations)} != len(qprograms)={n}")

        return calibrations

    def _mapped_buses(self, qp_buses: set[str], mapping: dict[str, str] | None) -> set[str]:
        """Apply mapping (if any) to a qprogram's logical buses to get physical buses."""
        if not mapping:
            return set(qp_buses)

        return {mapping.get(b, b) for b in qp_buses}

    def execute_qprograms_parallel(
        self,
        qprograms: list[QProgram],
        bus_mappings: list[dict[str, str] | None] | dict[str, str] | None = None,
        calibrations: list[Calibration | None] | Calibration | None = None,
        debug: bool = False,
    ) -> list[QProgramResults]:
        """Compiles a list of qprograms to be executed in parallel. Then it calls the execute_compilation_outputs_parallel method to execute the compiled qprograms.
        It loads each qprogram into a different sequencer and uses the multiplexing capabilities of QBlox to run all sequencers at the same time.

        **The execution can be done for (buses associated to) Qblox only. And it can only be done for qprograms that do not share buses.**

        Args:
            qprograms (list[QProgram]): A list of the :class:`.QProgram` to execute.
            bus_mapping (ist[dict[str, str] | None] | dict[str, str], optional). It can be one of the following:
                A list of dictionaries mapping the buses in the :class:`.QProgram` (keys )to the buses in the platform (values). In this case, each bus mapping gets assigned to the :class:`.QProgram` in the same index of the list of qprograms passed as first parameter.
                A single dictionary mapping the buses in the :class:`.QProgram` (keys )to the buses in the platform (values). In this case the same bus mapping is used for each one of the qprograms.
                None, in this case there is not a bus mapping between :class:`.QProgram` (keys )to the buses in the platform (values) and the buses are as defined in each qprogram.
                It is useful for mapping a generic :class:`.QProgram` to a specific experiment.
                Defaults to None.
            calibrations (list[Calibration], Calibration, optional). Contains information of previously calibrated values, like waveforms, weights and crosstalk matrix. It can be one of the following:
                A list of :class:`.Calibration` instances, one per :class:`.QProgram` instance in the qprograms parameter.
                A single instance of :class:`.Calibration`, in this case the same `.Calibration` instance gets associated to all qprograms.
                None. In this case no `.Calibration` instance is used.
                Defaults to None.
            debug (bool, optional): Whether to create debug information. For ``Qblox`` clusters all the program information is printed on screen.
                Defaults to False.

        Returns:
            QProgramResults: The results of the execution. ``QProgramResults.results()`` returns a list of dictionary (``dict[str, list[Result]]``) of measurement results.
            Each element of the list corresponds to a sequencer.
            The keys correspond to the buses a measurement were performed upon, and the values are the list of measurement results in chronological order.
        """
        if not qprograms:
            return []

        # Normalize mappings and calibrations to one-per-qprogram
        bus_mapping_list = self._normalize_bus_mappings(bus_mappings=bus_mappings, n=len(qprograms))
        calibrations_list = self._normalize_calibrations(calibrations=calibrations, n=len(qprograms))

        # Validate: no shared *physical* buses after applying each mapping
        all_physical: set[str] = set()
        if bus_mapping_list:
            for qp, bus_mapping in zip(qprograms, bus_mapping_list):
                phys = self._mapped_buses(qp.buses, bus_mapping)  # qp.buses is the set of logical buses
                if all_physical & phys:
                    raise ValueError(
                        f"QPrograms cannot be executed in parallel (bus collision on {all_physical & phys})."
                    )
                all_physical |= phys

            outputs = [
                self.compile_qprogram(qprogram=qp, bus_mapping=bus_mapping, calibration=calibration)
                for qp, bus_mapping, calibration in zip(qprograms, bus_mapping_list, calibrations_list)
            ]

        if any(isinstance(output.quantum_machines, QuantumMachinesCompilationOutput) for output in outputs):
            raise ValueError("Parallel execution is not supported in Quantum Machines.")

        return self.execute_compilation_outputs_parallel(
            outputs=cast("list[QbloxCompilationOutput]", [output.qblox for output in outputs]), debug=debug
        )

    def execute_compilation_outputs_parallel(self, outputs: list[QbloxCompilationOutput], debug: bool = False):
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
        buses_per_qprogram = self._resolve_qblox_parallel_buses(sequences_per_qprogram=sequences_per_qprogram)
        self._apply_qblox_distortions_parallel(
            sequences_per_qprogram=sequences_per_qprogram, buses_per_qprogram=buses_per_qprogram
        )

        if debug:
            self._write_qblox_parallel_debug(sequences_per_qprogram=sequences_per_qprogram)

        # Upload sequences
        self._upload_qblox_parallel_sequences(
            sequences_per_qprogram=sequences_per_qprogram, buses_per_qprogram=buses_per_qprogram
        )

        # Execute sequences
        self._run_qblox_parallel_sequences(
            sequences_per_qprogram=sequences_per_qprogram, buses_per_qprogram=buses_per_qprogram
        )

        # Acquire results
        results = self._acquire_qblox_parallel_results(
            outputs=outputs,
            buses_per_qprogram=buses_per_qprogram,
            aquisitions_per_qprogram=aquisitions_per_qprogram,
        )

        # Reset instrument settings
        self._reset_qblox_parallel_sequencers(
            sequences_per_qprogram=sequences_per_qprogram, buses_per_qprogram=buses_per_qprogram
        )

        return results

    def _resolve_qblox_parallel_buses(self, sequences_per_qprogram: list[dict[str, Any]]) -> list[dict[str, Bus]]:
        return [
            {bus_alias: self.buses.get(alias=bus_alias) for bus_alias in sequences}
            for sequences in sequences_per_qprogram
        ]

    def _apply_qblox_distortions_parallel(
        self,
        sequences_per_qprogram: list[dict[str, Any]],
        buses_per_qprogram: list[dict[str, Bus]],
    ) -> None:
        for qprogram_idx, buses in enumerate(buses_per_qprogram):
            for bus_alias, bus in buses.items():
                if bus.distortions:
                    for distortion in bus.distortions:
                        for waveform in sequences_per_qprogram[qprogram_idx][bus_alias]._waveforms._waveforms:
                            sequences_per_qprogram[qprogram_idx][bus_alias]._waveforms.modify(
                                waveform.name, distortion.apply(waveform.data)
                            )

    def _write_qblox_parallel_debug(self, sequences_per_qprogram: list[dict[str, Any]]) -> None:
        with open("debug_qblox_execution.txt", "w", encoding="utf-8") as sourceFile:
            for qprogram_idx, sequences in enumerate(sequences_per_qprogram):
                print(f"QProgram {qprogram_idx}:", file=sourceFile)
                for bus_alias, sequence in sequences.items():
                    print(f"Bus {bus_alias}:", file=sourceFile)
                    print(str(sequence._program), file=sourceFile)
                    print(file=sourceFile)

    def _upload_qblox_parallel_sequences(
        self,
        sequences_per_qprogram: list[dict[str, Any]],
        buses_per_qprogram: list[dict[str, Bus]],
    ) -> None:
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
                        instrument.sync_sequencer(sequencer_id=int(channel))  # type: ignore[arg-type]

    def _run_qblox_parallel_sequences(
        self,
        sequences_per_qprogram: list[dict[str, Any]],
        buses_per_qprogram: list[dict[str, Bus]],
    ) -> None:
        for qprogram_idx, sequences in enumerate(sequences_per_qprogram):
            for bus_alias in sequences:
                buses_per_qprogram[qprogram_idx][bus_alias].run()

    def _acquire_qblox_parallel_results(
        self,
        outputs: list[QbloxCompilationOutput],
        buses_per_qprogram: list[dict[str, Bus]],
        aquisitions_per_qprogram: list[dict[str, Any]],
    ) -> list[QProgramResults]:
        results = [QProgramResults() for _ in outputs]
        for qprogram_idx, buses in enumerate(buses_per_qprogram):
            for bus_alias, bus in buses.items():
                if bus.has_adc():
                    for instrument, channel in zip(buses[bus_alias].instruments, buses[bus_alias].channels):
                        if isinstance(instrument, QbloxModule):
                            bus_results = bus.acquire_qprogram_results(
                                acquisitions=aquisitions_per_qprogram[qprogram_idx][bus_alias], channel_id=int(channel)  # type: ignore[arg-type]
                            )
                            for bus_result in bus_results:
                                for _, acquisition_data in aquisitions_per_qprogram[qprogram_idx][bus_alias].items():
                                    intertwined = acquisition_data.intertwined
                                    unintertwined_results = self._unintertwined_qblox_results(bus_result, intertwined)  # type: ignore[arg-type]
                                    for unintertwined_result in unintertwined_results:
                                        results[qprogram_idx].append_result(bus=bus_alias, result=unintertwined_result)
        return results

    def _reset_qblox_parallel_sequencers(
        self,
        sequences_per_qprogram: list[dict[str, Any]],
        buses_per_qprogram: list[dict[str, Bus]],
    ) -> None:
        for qprogram_idx, sequences in enumerate(sequences_per_qprogram):
            for bus_alias in sequences:
                for instrument, channel in zip(
                    buses_per_qprogram[qprogram_idx][bus_alias].instruments,
                    buses_per_qprogram[qprogram_idx][bus_alias].channels,
                ):
                    if isinstance(instrument, QbloxModule):
                        instrument.desync_sequencer(sequencer_id=int(channel))  # type: ignore[arg-type]

    def execute_circuit(
        self, circuit: Circuit, nshots: int = 1000, *, qubit_mapping: dict[int, int] | None = None
    ) -> dict[str, int]:
        # Compile pulse schedule
        qprogram, logical_to_physical_mapping = self.compile_circuit(circuit, nshots, qubit_mapping=qubit_mapping)

        results = self.execute_qprogram(qprogram)

        samples = qprogram_results_to_samples(results, logical_to_physical_mapping)

        return samples

    def compile_circuit(
        self, circuit: Circuit, nshots: int, *, qubit_mapping: dict[int, int] | None = None
    ) -> tuple[QProgram, dict[int, int]]:
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

        Returns:
            tuple[dict, list[int] | None]: Tuple containing the dictionary of compiled assembly programs (The key is the bus alias (``str``),
                and the value is the assembly compilation (``list``)), and its corresponding final layout (Initial Re-mapping + SWAPs routing) of
                the Original Logical Qubits (l_q) in the physical circuit (wires): [l_q in wire 0, l_q in wire 1, ...] (None = trivial mapping).

        Raises:
            ValueError: raises value error if the circuit execution time is longer than ``repetition_duration`` for some qubit.
        """
        if self.digital_compilation_settings is None:
            raise ValueError("Cannot compile Circuit without defining DigitalCompilationSettings.")

        transpiler = CircuitTranspiler(self.digital_compilation_settings, qubit_mapping=qubit_mapping)
        transpiled_circuit = transpiler.run(circuit)

        compiler = CircuitToQProgramCompiler(self.digital_compilation_settings)
        qprogram = compiler.compile(transpiled_circuit, nshots)

        return qprogram, transpiler.context.final_layout

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
            acquisition_showing (bool): Allows visualizing the acquisition period on the plot. Defaults to True.
            bus_mapping (dict[str, str], optional): A dictionary mapping the buses in the :class:`.QProgram` (keys )to the buses in the platform (values).
                It is useful for mapping a generic :class:`.QProgram` to a specific experiment. Defaults to None.

        Returns:
            plotly object: plotly.graph_objs._figure.Figure
        """
        runcard_data = self._data_draw()
        qblox_draw = QbloxDraw()
        sequencer = self.compile_qprogram(qprogram, bus_mapping, calibration).qblox
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
            description (str | None, optional): String containing a description or any relevant information about the experiment. Defaults to None.

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
            description (str | None, optional): String containing a description or any relevant information about the experiment. Defaults to None.
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
                    f"Loops dimensions must be the same than the array introduced, {loop_name} as {loop_array.shape[0]} != {shape[iteration]}"  # type: ignore
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
