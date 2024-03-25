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

"""Quantum Machines Manager class."""
import os
from dataclasses import dataclass
from typing import Any, Dict, cast

import numpy as np
from qm import DictQuaConfig, QuantumMachine, QuantumMachinesManager, SimulationConfig
from qm.jobs.running_qm_job import RunningQmJob
from qm.octave import QmOctaveConfig
from qm.qua import Program

from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName, Parameter, QMMDriver
from qililab.utils import hash_qua_program, merge_dictionaries


@InstrumentFactory.register
class QuantumMachinesCluster(Instrument):
    """Class defining the Qililab Quantum Machines Cluster instrument in Qililab.

    This class allows Qililab control and communication with an instance of the
    Quantum Machines Manager, which is the central class to interact with Quantum Machines instruments.
    The manager is responsible, through the use of QUA sequences, of setting the Quantum Machines instruments
    in the right manner for Quantum Control.

    Args:
        name (InstrumentName): Name of the Instrument.
        device (QMMDriver): Instance of the Quantum Machines Manager Driver class.
        settings (QMMSettings): Settings of the instrument.
    """

    name = InstrumentName.QUANTUM_MACHINES_CLUSTER

    @dataclass
    class QuantumMachinesClusterSettings(Instrument.InstrumentSettings):
        """Settings for Quantum Machines Cluster instrument.

        Args:
            address (str): IP address to connect to the Quantum Machines instruments.
            cluster (str): Name of the cluster to connect to.
            run_octave_calibration (bool): Flag to indicate if octave calibration should be run on connecting to Quantum Machines.
            octaves (list[dict[str, Any]]): List of octaves the quantum machines stack has.
            controllers (list[dict[str, Any]]): List of controllers (instruments) the quantum machines stack has.
            elements (list[dict[str, Any]]): List of elements (buses) the quantum machines stack has.
        """

        address: str
        cluster: str
        run_octave_calibration: bool
        octaves: list[dict[str, Any]]
        controllers: list[dict[str, Any]]
        elements: list[dict[str, Any]]

        def to_qua_config(self) -> Dict[str, Any]:
            """Creates the Quantum Machines QUA config dictionary.

            Creates, an instance of a dictionary in the format that QuantumMachines expects the config dictionary to be.

            The values of following keys of the dictionary are parsed from QMMSettings:
                - controllers (OPX+ instruments)
                - octaves (Octave instruments)
                - mixers (up/down conversion settings if not using octaves)
                - elements (buses)

            The values of the rest keys are empty, meant to be updated in runtime.

            Returns:
                config: Dict[str, Any]
            """
            elements, mixers = self._get_elements_and_mixers_config()
            controllers = self._get_controllers_config()
            octaves = self._get_octaves_config()

            return {
                "version": 1,
                "controllers": controllers,
                "elements": elements,
                "mixers": mixers,
                "waveforms": {},
                "integration_weights": {},
                "pulses": {},
                "digital_waveforms": {},
                "octaves": octaves,
            }

        def _get_controllers_config(self) -> dict[str, Any]:
            """Returns the controllers config dictionary.

            Returns:
                controllers: Dict[str, Any]
            """
            return {
                controller["name"]: {
                    "analog_outputs": {
                        output["port"]: {
                            "offset": output["offset"] if "offset" in output else 0.0,
                            "delay": output["delay"] if "delay" in output else 0.0,
                        }
                        for output in controller.get("analog_outputs", [])
                    },
                    "analog_inputs": {
                        input["port"]: {
                            "offset": input["offset"] if "offset" in input else 0.0,
                            "gain_db": input["gain"] if "gain" in input else 0.0,
                        }
                        for input in controller.get("analog_inputs", [])
                    },
                    "digital_outputs": {output["port"]: {} for output in controller.get("digital_outputs", [])},
                }
                for controller in self.controllers
            }

        def _get_octaves_config(self) -> dict[str, Any]:
            """Returns the octaves config dictionary.

            Returns:
                octaves: Dict[str, Any]
            """
            return {
                octave["name"]: {
                    "RF_outputs": {
                        output["port"]: {
                            "LO_frequency": output["lo_frequency"],  # Should be between 2 and 18 GHz.
                            "LO_source": "internal",
                            "gain": output["gain"] if "gain" in output else 0.0,
                            "output_mode": "always_on",
                            "input_attenuators": "OFF",  # can be: "OFF" / "ON". Default is "OFF".
                        }
                        for output in octave.get("rf_outputs", [])
                    },
                    "RF_inputs": {
                        output["port"]: {
                            "RF_source": "RF_in",
                            "LO_frequency": output["lo_frequency"],
                            "LO_source": "internal",  # can be: "internal" / "external". Default is "internal".
                            "IF_mode_I": "direct",  # can be: "direct" / "mixer" / "envelope" / "off". Default is "direct".
                            "IF_mode_Q": "direct",
                        }
                        for output in octave.get("rf_inputs", [])
                    },
                    "connectivity": octave["controller"],
                }
                for octave in self.octaves
            }

        def _get_elements_and_mixers_config(self) -> tuple:
            """Returns the elements config dictionary.

            Returns:
                elements: Dict[str, Any]
            """
            elements = {}
            mixers = {}

            for element in self.elements:
                bus_name = element["bus"]
                element_dict: dict = {"operations": {}}

                # Flux bus
                if "single_input" in element:
                    element_dict["singleInput"] = {
                        "port": (element["single_input"]["controller"], element["single_input"]["port"]),
                    }
                # IQ bus
                elif "mix_inputs" in element:
                    mixer_name = f"mixer_{bus_name}"
                    lo_frequency = int(element["mix_inputs"]["lo_frequency"])
                    intermediate_frequency = int(element["intermediate_frequency"])
                    mixer_correction = (
                        element["mix_inputs"]["mixer_correction"]
                        if "mixer_correction" in element["mix_inputs"]
                        else [1.0, 0.0, 0.0, 1.0]
                    )
                    mixers[mixer_name] = [
                        {
                            "intermediate_frequency": intermediate_frequency,
                            "lo_frequency": lo_frequency,
                            "correction": mixer_correction,
                        }
                    ]
                    element_dict["mixInputs"] = {
                        key: (element["mix_inputs"][key]["controller"], element["mix_inputs"][key]["port"])
                        for key in ["I", "Q"]
                    } | {"lo_frequency": lo_frequency, "mixer": mixer_name}
                    element_dict["intermediate_frequency"] = intermediate_frequency

                    # readout bus
                    if "outputs" in element:
                        element_dict["outputs"] = {
                            key: (element["outputs"][key]["controller"], element["outputs"][key]["port"])
                            for key in ["out1", "out2"]
                        }
                        element_dict["time_of_flight"] = element["time_of_flight"]
                        element_dict["smearing"] = element["smearing"]
                # RF with Octave
                elif "rf_inputs" in element:
                    element_dict["RF_inputs"] = {"port": (element["rf_inputs"]["octave"], element["rf_inputs"]["port"])}
                    element_dict["intermediate_frequency"] = int(element["intermediate_frequency"])

                    # readout bus
                    if "rf_outputs" in element:
                        element_dict["RF_outputs"] = {
                            "port": (element["rf_outputs"]["octave"], element["rf_outputs"]["port"]),
                        }
                        element_dict["time_of_flight"] = element["time_of_flight"]
                        element_dict["smearing"] = element["smearing"]

                # other settings
                if "digital_inputs" in element:
                    element_dict["digitalInputs"] = {
                        "switch": {
                            "port": (element["digital_inputs"]["controller"], element["digital_inputs"]["port"]),
                            "delay": element["digital_inputs"]["delay"],
                            "buffer": element["digital_inputs"]["buffer"],
                        }
                    }
                if "digital_outputs" in element:
                    element_dict["digitalOutputs"] = {
                        "port": (element["digital_outputs"]["controller"], element["digital_outputs"]["port"]),
                    }

                elements[bus_name] = element_dict

            return elements, mixers

    settings: QuantumMachinesClusterSettings
    device: QMMDriver
    _qmm: QuantumMachinesManager
    _qm: QuantumMachine
    _config: DictQuaConfig
    _octave_config: QmOctaveConfig | None = None
    _is_connected_to_qm: bool = False
    _compiled_program_cache: dict[str, str] = {}

    @property
    def config(self) -> DictQuaConfig:
        """Get the QUA config dictionary."""
        return self._config

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Sets initial instrument settings.

        Creates an instance of the Qilililab Quantum Machines Manager, and sets the configuration dictionary.
        """
        if self.settings.octaves:
            self._octave_config = QmOctaveConfig()
            self._octave_config.set_calibration_db(os.getcwd())
            for octave in self.settings.octaves:
                self._octave_config.add_device_info(octave["name"], self.settings.address, octave["port"])
        self._qmm = QuantumMachinesManager(
            host=self.settings.address, cluster_name=self.settings.cluster, octave=self._octave_config
        )

        self._config = self.settings.to_qua_config()

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Turns on the instrument."""
        if not self._is_connected_to_qm:
            self._qm = self._qmm.open_qm(config=self._config, close_other_machines=True)
            self._compiled_program_cache = {}
            self._is_connected_to_qm = True

            if self.settings.run_octave_calibration:
                self.run_octave_calibration()

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Resets instrument settings."""

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Turns off an instrument."""
        if self._is_connected_to_qm:
            self._qm.close()
            self._is_connected_to_qm = False

    def append_configuration(self, configuration: dict):
        """Update the configuration dictionary by appending the configuration generated by compilation."""
        merged_configuration = merge_dictionaries(dict(self._config), configuration)
        if self._config != merged_configuration:
            self._config = cast(DictQuaConfig, merged_configuration)
            # If we are already connected, reopen the connection with the new configuration
            if self._is_connected_to_qm:
                self._qm = self._qmm.open_qm(config=self._config, close_other_machines=True)
                self._compiled_program_cache = {}

    def run_octave_calibration(self):
        """Run calibration procedure for the buses with octaves, if any."""
        elements = [element for element in self._config["elements"] if "RF_inputs" in self._config["elements"][element]]
        for element in elements:
            self._qm.calibrate_element(element)

    def set_parameter_of_bus(self, bus: str, parameter: Parameter, value: float | str | bool):
        """Sets the parameter of the instrument

        Args:
            bus (str): The assossiated bus to change parameter
            parameter (Parameter): The parameter to update
            value (float | str | bool): The new value of the parameter

        Raises:
            NotImplementedError: Raised if not connected to Quantum Machines
            ParameterNotFound: Raised if parameter does not exist
        """
        # TODO: Change private QM API to public when implemented.
        if not self._is_connected_to_qm:
            raise NotImplementedError(f"You should be connected to {self.name} in order to change a parameter.")

        element = next((element for element in self.settings.elements if element["bus"] == bus), None)
        if element is None:
            raise ValueError(f"Bus {bus} was not found in {self.name} settings.")

        if parameter in [Parameter.LO_FREQUENCY, Parameter.GAIN]:
            if "rf_inputs" not in element:
                raise ValueError(
                    f"Trying to change parameter {parameter.name} in {self.name}, however bus {bus} is not connected to an octave."
                )
            octave_name = element["rf_inputs"]["octave"]
            out_port = element["rf_inputs"]["port"]
            in_port = element["rf_outputs"]["port"] if "rf_outputs" in element else None
            settings_octave = next(octave for octave in self.settings.octaves if octave["name"] == octave_name)
            settings_octave_rf_output = next(
                rf_output for rf_output in settings_octave["rf_outputs"] if rf_output["port"] == out_port
            )

            if parameter == Parameter.LO_FREQUENCY:
                lo_frequency = float(value)
                self._qm.octave.set_lo_frequency(element=bus, lo_frequency=lo_frequency)
                settings_octave_rf_output["lo_frequency"] = lo_frequency
                self._config["octaves"][octave_name]["RF_outputs"][out_port]["LO_frequency"] = lo_frequency

                if in_port is not None:
                    settings_octave_rf_input = next(
                        rf_input for rf_input in settings_octave["rf_inputs"] if rf_input["port"] == in_port
                    )
                    settings_octave_rf_input["lo_frequency"] = lo_frequency
                    self._config["octaves"][octave_name]["RF_inputs"][in_port]["LO_frequency"] = lo_frequency
                return
            if parameter == Parameter.GAIN:
                gain_in_db = float(value)
                self._qm.octave.set_rf_output_gain(element=bus, gain_in_db=gain_in_db)
                settings_octave_rf_output["gain"] = gain_in_db
                self._config["octaves"][octave_name]["RF_outputs"][out_port]["gain"] = gain_in_db
                return
        if parameter == Parameter.IF:
            intermediate_frequency = float(value)
            self._qm.set_intermediate_frequency(element=bus, freq=intermediate_frequency)
            element["intermediate_frequency"] = intermediate_frequency
            self._config["elements"][bus]["intermediate_frequency"] = intermediate_frequency
            return
        raise ParameterNotFound(f"Could not find parameter {parameter} in instrument {self.name}.")

    def get_parameter_of_bus(self, bus: str, parameter: Parameter):
        """Gets the value of a parameter

        Args:
            bus (str): The assossiated bus of the parameter
            parameter (Parameter): The parameter to get value

        Raises:
            ParameterNotFound: Raised if parameter does not exist
        """
        # TODO: Change private QM API to public when implemented.
        if parameter == Parameter.LO_FREQUENCY:
            return self._qm._elements[bus].input.lo_frequency  # type: ignore[union-attr] # pylint: disable=protected-access
        if parameter == Parameter.GAIN:
            return self._qm._elements[bus].input.gain  # type: ignore[union-attr] # pylint: disable=protected-access
        if parameter == Parameter.IF:
            return self._qm._elements[bus].intermediate_frequency  # pylint: disable=protected-access
        raise ParameterNotFound(f"Could not find parameter {parameter} in instrument {self.name}")

    def compile(self, program: Program) -> str:
        """Compiles and stores a given QUA program on the Quantum Machines instance,
        and returns a unique identifier associated with the compiled program.

        The method first generates a hash for the input QUA program. If this hash is not already present in
        the cache, it proceeds to compile the program using QM's compile method and stores the result in the cache
        indexed by the generated hash. This caching mechanism prevents recompiling the same program multiple times,
        thus optimizing performance.

        Args:
            program (Program): The QUA program to be compiled.

        Returns:
            str: A unique identifier (hash) for the compiled QUA program. This identifier can be used to retrieve the compiled program from the cache, or run it  with `run_compiled_program` method.
        """
        qua_program_hash = hash_qua_program(program=program)
        if qua_program_hash not in self._compiled_program_cache:
            self._compiled_program_cache[qua_program_hash] = self._qm.compile(program=program)
        return self._compiled_program_cache[qua_program_hash]

    def run_compiled_program(self, compiled_program_id: str) -> RunningQmJob:
        """Executes a previously compiled QUA program identified by its unique compiled program ID.

        This method submits the compiled program to the Quantum Machines (QM) execution queue and waits for
        its execution to complete. The execution of the program is managed by the QM's queuing system,
        which schedules and runs the job on the quantum hardware or simulator as per availability and queue status.

        Args:
            compiled_program_id (str): The unique identifier of the compiled QUA program to be executed. This ID should correspond to a program that has already been compiled and is present in the program cache.

        Returns:
            RunningQmJob: An object representing the running job. This object provides methods and properties to check the status of the job, retrieve results upon completion, and manage or investigate the job's execution.
        """
        pending_job = self._qm.queue.add_compiled(compiled_program_id)
        return pending_job.wait_for_execution()

    def run(self, program: Program) -> RunningQmJob:
        """Runs the QUA Program.

        Creates, for every execution, an instance of a QuantumMachine class and executes the QUA program on it.
        After execution, the job generated by the Quantum Machines Manager is returned.

        Args:
            program (Program): QUA Program to be run on Quantum Machines instruments.

        Returns:
            job: Quantum Machines job.
        """

        return self._qm.execute(program)

    def get_acquisitions(self, job: RunningQmJob) -> dict[str, np.ndarray]:
        """Fetches the results from the execution of a QUA Program.

        Once the results have been fetched, they are returned wrapped in a QuantumMachinesResult instance.

        Args:
            job (QmJob): Job that provides the result handles.

        Returns:
            QuantumMachinesResult: Quantum Machines result instance.
        """
        result_handles_fetchers = job.result_handles
        result_handles_fetchers.wait_for_all_values()
        results = {
            name: handle.fetch_all(flat_struct=True) for name, handle in job.result_handles if handle is not None
        }
        return {name: data for name, data in results.items() if data is not None}

    def simulate(self, program: Program) -> RunningQmJob:
        """Simulates the QUA Program.

        Creates, for every simulation, an instance of a QuantumMachine class and executes the QUA program on it.
        It returns the running job instance.

        Args:
            program (Program): QUA Program to be simulated on Quantum Machines instruments.

        Returns:
            job: Quantum Machines job.
        """
        return self._qm.simulate(program, SimulationConfig(40_000))
