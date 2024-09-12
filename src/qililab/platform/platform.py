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

# pylint: disable=too-many-lines
"""Platform class."""
import ast
import datetime
import io
import re
import time
import traceback
import warnings
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from queue import Queue
from typing import Callable

import numpy as np
from qibo.gates import M
from qibo.models import Circuit
from qm import generate_qua_script
from qm.exceptions import StreamProcessingDataLossError
from qpysequence import Sequence as QpySequence
from ruamel.yaml import YAML

from qililab.analog import AnnealingProgram
from qililab.chip import Chip
from qililab.circuit_transpiler import CircuitTranspiler
from qililab.config import logger
from qililab.constants import FLUX_CONTROL_REGEX, GATE_ALIAS_REGEX, RUNCARD
from qililab.exceptions import ExceptionGroup
from qililab.instrument_controllers import InstrumentController, InstrumentControllers
from qililab.instrument_controllers.utils import InstrumentControllerFactory
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.instruments.qblox import QbloxModule
from qililab.instruments.quantum_machines import QuantumMachinesCluster
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseSchedule
from qililab.pulse import QbloxCompiler as PulseQbloxCompiler
from qililab.qprogram import Calibration, Domain, Experiment, QbloxCompiler, QProgram, QuantumMachinesCompiler
from qililab.qprogram.experiment_executor import ExperimentExecutor
from qililab.result import Result
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.result.qprogram.qprogram_results import QProgramResults
from qililab.result.qprogram.quantum_machines_measurement_result import QuantumMachinesMeasurementResult
from qililab.settings import Runcard
from qililab.system_control import ReadoutSystemControl
from qililab.typings.enums import InstrumentName, Line, Parameter
from qililab.utils import hash_qpy_sequence
from qililab.waveforms import IQPair, Square

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

    def __init__(self, runcard: Runcard):
        self.name = runcard.name
        """Name of the platform (``str``) """

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

        self.flux_to_bus_topology = runcard.flux_control_topology
        """Flux to bus mapping for analog control"""

        self._connected_to_instruments: bool = False
        """Boolean indicating the connection status to the instruments. Defaults to False (not connected)."""

        if any(isinstance(instrument, QbloxModule) for instrument in self.instruments.elements):
            self.compiler = PulseQbloxCompiler(platform=self)  # TODO: integrate with qprogram compiler
            """Compiler to translate given programs to instructions for a given awg vendor."""

        self._qpy_sequence_cache: dict[str, str] = {}
        """Dictionary for caching qpysequences."""

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
        logger.info("Disconnected from instruments")

    def get_element(self, alias: str):
        """Gets the platform element and to which bus it is connected, using its alias.

        Args:
            alias (str): Element alias to identify it.

        Returns:
            tuple[object, list | None]: Element class together with the index of the bus where the element is located.
        """
        # TODO: fix docstring, bus is not returned in most cases
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
            regex_match = re.search(FLUX_CONTROL_REGEX, alias)
            if regex_match is not None:
                element_type = regex_match.lastgroup
                element_shorthands = {"qubit": "q", "coupler": "c"}
                flux = regex_match["flux"]
                # TODO: support commuting the name of the coupler eg. c1_0 = c0_1
                return self._get_bus_by_alias(
                    next(
                        (
                            element.bus
                            for element in self.flux_to_bus_topology  # type: ignore[union-attr]
                            if element.flux == f"{flux}_{element_shorthands[element_type]}{regex_match[element_type]}"  # type: ignore[index]
                        ),
                        None,
                    )
                )

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
        gates_settings_dict = {RUNCARD.GATES_SETTINGS: self.gates_settings.to_dict()}
        chip_dict = {RUNCARD.CHIP: self.chip.to_dict() if self.chip is not None else None}
        buses_dict = {RUNCARD.BUSES: self.buses.to_dict() if self.buses is not None else None}
        instrument_dict = {RUNCARD.INSTRUMENTS: self.instruments.to_dict() if self.instruments is not None else None}
        instrument_controllers_dict = {
            RUNCARD.INSTRUMENT_CONTROLLERS: (
                self.instrument_controllers.to_dict() if self.instrument_controllers is not None else None
            ),
        }
        flux_control_topology_dict = {
            RUNCARD.FLUX_CONTROL_TOPOLOGY: (
                [flux_control.to_dict() for flux_control in self.flux_to_bus_topology]
                if self.flux_to_bus_topology is not None
                else None
            )
        }

        return (
            name_dict
            | gates_settings_dict
            | chip_dict
            | buses_dict
            | instrument_dict
            | instrument_controllers_dict
            | flux_control_topology_dict
        )

    def __str__(self) -> str:
        """String representation of the platform.

        Returns:
            str: Name of the platform.
        """
        return str(YAML().dump(self.to_dict(), io.BytesIO()))

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
            print(f"An error occurred: {e}")
            raise  # Re-raise the exception for further handling
        finally:
            # Call the cleanup methods in reverse order
            for cleanup_method in reversed(cleanup_methods):
                try:
                    cleanup_method()
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"Error during cleanup: {e}")
                    cleanup_errors.append(e)

            # Raise any exception that might have happened during cleanup
            if cleanup_errors:
                raise ExceptionGroup("Exceptions occurred during cleanup", cleanup_errors)

    def execute_anneal_program(  # pylint: disable=too-many-locals
        self,
        annealing_program_dict: list[dict[str, dict[str, float]]],
        calibration: Calibration,
        readout_bus: str,
        measurement_name: str,
        transpiler: Callable,
        num_averages: int,
        num_shots: int = 1,
        weights: str | None = None,
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
        """
        if self.flux_to_bus_topology is None:
            raise ValueError("Flux to bus topology not given in the runcard")
        if calibration.has_waveform(bus=readout_bus, name=measurement_name):
            annealing_program = AnnealingProgram(
                flux_to_bus_topology=self.flux_to_bus_topology, annealing_program=annealing_program_dict
            )
            annealing_program.transpile(transpiler)
            crosstalk_matrix = (
                calibration.crosstalk_matrix.inverse() if calibration.crosstalk_matrix is not None else None
            )
            annealing_waveforms = annealing_program.get_waveforms(crosstalk_matrix=crosstalk_matrix)

            qp_annealing = QProgram()
            shots_variable = qp_annealing.variable("num_shots", Domain.Scalar, int)

            with qp_annealing.for_loop(variable=shots_variable, start=0, stop=num_shots, step=1):
                with qp_annealing.average(num_averages):
                    for bus, waveform in annealing_waveforms.items():
                        qp_annealing.play(bus=bus, waveform=waveform)
                    qp_annealing.sync()
                    if weights and calibration.has_weights(bus=readout_bus, name=weights):
                        qp_annealing.measure(bus=readout_bus, waveform=measurement_name, weights=weights)
                    else:
                        r_duration = calibration.get_waveform(bus=readout_bus, name=measurement_name).get_duration()
                        weights_shape = Square(amplitude=1, duration=r_duration)
                        qp_annealing.measure(
                            bus=readout_bus, waveform=measurement_name, weights=IQPair(I=weights_shape, Q=weights_shape)
                        )

            return self.execute_qprogram(qprogram=qp_annealing, calibration=calibration)
        raise ValueError("The calibrated measurement is not present in the calibration file.")

    def execute_experiment(self, experiment: Experiment, results_path: str) -> str:
        """Executes the given quantum experiment and saves the results.

        This method initializes an `ExperimentExecutor` with the provided `experiment` and `results_path`,
        and then executes the experiment. The results are streamed to the specified path in real-time.

        Args:
            experiment (Experiment): The quantum experiment to be executed.
            results_path (str): The path where the experiment's results will be saved.

        Returns:
            str: The path of the file that the experiment's results are stored.
        """
        executor = ExperimentExecutor(platform=self, experiment=experiment, results_path=results_path)
        return executor.execute()

    def execute_qprogram(  # pylint: disable=too-many-locals
        self,
        qprogram: QProgram,
        bus_mapping: dict[str, str] | None = None,
        calibration: Calibration | None = None,
        dataloss_tries: int = 3,
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
        bus_aliases = {bus_mapping[bus] if bus_mapping and bus in bus_mapping else bus for bus in qprogram.buses}
        buses = [self._get_bus_by_alias(alias=bus_alias) for bus_alias in bus_aliases]
        instruments = {
            instrument
            for bus in buses
            for instrument in bus.system_control.instruments
            if isinstance(instrument, (QbloxModule, QuantumMachinesCluster))
        }
        if all(isinstance(instrument, QbloxModule) for instrument in instruments):
            # Retrieve the time of flight parameter from settings
            times_of_flight = {
                bus.alias: int(bus.get_parameter(Parameter.TIME_OF_FLIGHT))
                for bus in buses
                if isinstance(bus.system_control, ReadoutSystemControl)
            }
            delays = {bus.alias: int(bus.get_parameter(Parameter.DELAY)) for bus in buses}
            # Determine what should be the initial value of the markers for each bus.
            # This depends on the model of the associated Qblox module and the `output` setting of the associated sequencer.
            markers = {}
            for bus in buses:
                for instrument in bus.system_control.instruments:
                    if isinstance(instrument, QbloxModule):
                        sequencers = instrument.get_sequencers_from_chip_port_id(bus.port)
                        if instrument.name == InstrumentName.QCMRF:
                            markers[bus.alias] = "".join(
                                ["1" if i in [0, 1] and i in sequencers[0].outputs else "0" for i in range(4)]
                            )[::-1]
                        elif instrument.name == InstrumentName.QRMRF:
                            markers[bus.alias] = "".join(
                                ["1" if i in [1] and i - 1 in sequencers[0].outputs else "0" for i in range(4)]
                            )[::-1]
                        else:
                            markers[bus.alias] = "0000"
            return self._execute_qprogram_with_qblox(
                qprogram=qprogram,
                times_of_flight=times_of_flight,
                delays=delays,
                markers=markers,
                bus_mapping=bus_mapping,
                calibration=calibration,
                debug=debug,
            )
        if all(isinstance(instrument, QuantumMachinesCluster) for instrument in instruments):
            if len(instruments) != 1:
                raise NotImplementedError(
                    "Executing QProgram in more than one Quantum Machines Cluster is not supported."
                )
            cluster: QuantumMachinesCluster = instruments.pop()  # type: ignore[assignment]
            threshold_rotations = {
                bus.alias: float(bus.get_parameter(parameter=Parameter.THRESHOLD_ROTATION))
                for bus in buses
                if isinstance(bus.system_control, ReadoutSystemControl)
            }  # type: ignore
            thresholds = {
                bus.alias: float(bus.get_parameter(parameter=Parameter.THRESHOLD))
                for bus in buses
                if isinstance(bus.system_control, ReadoutSystemControl)
            }  # type: ignore
            return self._execute_qprogram_with_quantum_machines(
                cluster=cluster,
                qprogram=qprogram,
                bus_mapping=bus_mapping,
                threshold_rotations=threshold_rotations,  # type: ignore
                thresholds=thresholds,  # type: ignore
                calibration=calibration,
                dataloss_tries=dataloss_tries,
                debug=debug,
            )
        raise NotImplementedError("Executing QProgram in a mixture of instruments is not supported.")

    def _execute_qprogram_with_qblox(  # pylint: disable=too-many-locals
        self,
        qprogram: QProgram,
        times_of_flight: dict[str, int],
        delays: dict[str, int],
        markers: dict[str, str],
        bus_mapping: dict[str, str] | None = None,
        calibration: Calibration | None = None,
        debug: bool = False,
    ) -> QProgramResults:
        # Compile QProgram
        qblox_compiler = QbloxCompiler()
        sequences, acquisitions = qblox_compiler.compile(
            qprogram=qprogram,
            bus_mapping=bus_mapping,
            calibration=calibration,
            times_of_flight=times_of_flight,
            delays=delays,
            markers=markers,
        )
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
            # sync all relevant sequences
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
                bus_results = buses[bus_alias].acquire_qprogram_results(acquisitions=acquisitions[bus_alias])
                for bus_result in bus_results:
                    results.append_result(bus=bus_alias, result=bus_result)

        # Reset instrument settings
        for bus_alias in sequences:
            for instrument in buses[bus_alias].system_control.instruments:
                if isinstance(instrument, QbloxModule):
                    instrument.desync_by_port(buses[bus_alias].port)

        return results

    def _execute_qprogram_with_quantum_machines(  # pylint: disable=too-many-locals,dangerous-default-value
        self,
        cluster: QuantumMachinesCluster,
        qprogram: QProgram,
        bus_mapping: dict[str, str] | None = None,
        threshold_rotations: dict[str, float | None] = {},
        thresholds: dict[str, float | None] = {},
        calibration: Calibration | None = None,
        dataloss_tries: int = 3,
        debug: bool = False,
    ) -> QProgramResults:
        compiler = QuantumMachinesCompiler()
        qua_program, configuration, measurements = compiler.compile(
            qprogram=qprogram, bus_mapping=bus_mapping, threshold_rotations=threshold_rotations, calibration=calibration
        )

        start_time = datetime.datetime.now()
        for iteration in np.arange(dataloss_tries):  # TODO: This is a temporal fix as QM fixes the dataloss error
            try:
                cluster.append_configuration(configuration=configuration)

                if debug:
                    with open("debug_qm_execution.py", "w", encoding="utf-8") as sourceFile:
                        print(generate_qua_script(qua_program, cluster.config), file=sourceFile)

                compiled_program_id = cluster.compile(program=qua_program)
                job = cluster.run_compiled_program(compiled_program_id=compiled_program_id)

                acquisitions = cluster.get_acquisitions(job=job)

                results = QProgramResults()
                # Doing manual classification of results as QM does not return thresholded values like Qblox
                for measurement in measurements:
                    measurement_result = QuantumMachinesMeasurementResult(
                        *[acquisitions[handle] for handle in measurement.result_handles],
                    )
                    measurement_result.set_classification_threshold(thresholds.get(measurement.bus, None))
                    results.append_result(bus=measurement.bus, result=measurement_result)

                return results

            except StreamProcessingDataLossError as dataloss:
                time_interval = datetime.datetime.now() - start_time
                warnings.warn(
                    f"Warning: {dataloss} raised, retrying experiment ({iteration+1}/{dataloss_tries} available tries) after {time_interval.seconds} s"
                )
                warnings.warn(traceback.format_exc())
                if iteration + 1 != dataloss_tries:
                    time.sleep(1 * dataloss_tries)
                    start_time = datetime.datetime.now()
                    continue
                cluster.turn_off()
                raise dataloss
            except Exception as e:
                cluster.turn_off()
                raise e

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
