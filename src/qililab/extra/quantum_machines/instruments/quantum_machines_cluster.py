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

import hashlib
import os
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from qm import DictQuaConfig, QmJob, QuantumMachine, QuantumMachinesManager, SimulationConfig, generate_qua_script
from qm.api.v2.job_api import JobApi
from qm.jobs.running_qm_job import RunningQmJob
from qm.octave import QmOctaveConfig
from qm.program import Program

from qililab.instruments.decorators import check_device_initialized, log_set_parameter
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import ChannelID, InstrumentName, OutputID, Parameter, ParameterValue, QMMDriver
from qililab.utils import merge_dictionaries


def hash_qua_program(program: Program) -> str:
    """Hash a QUA program"""
    program_str = "\n".join(generate_qua_script(program).split("\n")[3:])
    return hashlib.md5(program_str.encode("utf-8"), usedforsecurity=False).hexdigest()


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
        timeout: int | None = None

        def to_qua_config(self) -> DictQuaConfig:
            """Creates the Quantum Machines QUA config dictionary.

            Creates, an instance of a dictionary in the format that QuantumMachines expects the config dictionary to be.

            The values of following keys of the dictionary are parsed from QMMSettings:
                - controllers (OPX+ instruments)
                - octaves (Octave instruments)
                - mixers (up/down conversion settings if not using octaves)
                - elements (buses)

            The values of the rest keys are empty, meant to be updated in runtime.

            Returns:
                config: DictQuaConfig
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
            controllers: dict = {}
            for controller in self.controllers:
                controller_type = controller["type"] if "type" in controller else "opx1"
                if controller_type == "opx1":
                    controllers[controller["name"]] = {
                        "analog_outputs": {
                            output["port"]: {
                                "offset": output["offset"] if "offset" in output else 0.0,
                                "delay": output["delay"] if "delay" in output else 0.0,
                                "filter": (
                                    {
                                        "feedforward": (
                                            output["filter"]["feedforward"] if "feedforward" in output["filter"] else []
                                        ),
                                        "feedback": (
                                            output["filter"]["feedback"] if "feedback" in output["filter"] else []
                                        ),
                                    }
                                    if "filter" in output
                                    else {"feedforward": [], "feedback": []}
                                ),
                                "shareable": output["shareable"] if "shareable" in output else False,
                            }
                            for output in controller.get("analog_outputs", [])
                        },
                        "analog_inputs": {
                            input["port"]: {
                                "offset": input["offset"] if "offset" in input else 0.0,
                                "gain_db": input["gain"] if "gain" in input else 0.0,
                                "shareable": input["shareable"] if "shareable" in input else False,
                            }
                            for input in controller.get("analog_inputs", [])
                        },
                        "digital_outputs": {output["port"]: {} for output in controller.get("digital_outputs", [])},
                    }
                elif controller_type == "opx1000":
                    controllers[controller["name"]] = {
                        "fems": {
                            fem["fem"]: {
                                "type": fem["type"] if "type" in fem else "LF",
                                "analog_outputs": {
                                    output["port"]: {
                                        "offset": output["offset"] if "offset" in output else 0.0,
                                        "delay": output["delay"] if "delay" in output else 0.0,
                                        "output_mode": output["output_mode"] if "output_mode" in output else "direct",
                                        "sampling_rate": output["sampling_rate"] if "sampling_rate" in output else 1e9,
                                        "upsampling_mode": (
                                            output["upsampling_mode"]
                                            if "upsampling_mode" in output
                                            else (
                                                "pulse"
                                                if "output_mode" in output and output["output_mode"] == "amplified"
                                                else "mw"
                                            )
                                        ),
                                        "filter": (
                                            {
                                                "feedforward": (
                                                    output["filter"]["feedforward"]
                                                    if "feedforward" in output["filter"]
                                                    else []
                                                ),
                                                "feedback": (
                                                    output["filter"]["feedback"]
                                                    if "feedback" in output["filter"]
                                                    else []
                                                ),
                                            }
                                            if "filter" in output
                                            else {"feedforward": [], "feedback": []}
                                        ),
                                        "shareable": fem["shareable"] if "shareable" in fem else False,
                                    }
                                    for output in fem.get("analog_outputs", [])
                                },
                                "analog_inputs": {
                                    input["port"]: {
                                        "offset": input["offset"] if "offset" in input else 0.0,
                                        "gain_db": input["gain"] if "gain" in input else 0.0,
                                        "sampling_rate": input["sampling_rate"] if "sampling_rate" in input else 1e9,
                                        "shareable": fem["shareable"] if "shareable" in fem else False,
                                    }
                                    for input in fem.get("analog_inputs", [])
                                },
                                "digital_outputs": {output["port"]: {} for output in fem.get("digital_outputs", [])},
                            }
                            for fem in controller["fems"]
                        }
                    }
            return controllers

        def _get_octaves_config(self) -> dict[str, Any]:
            """Returns the octaves config dictionary.

            Returns:
                octaves: Dict[str, Any]
            """
            octaves: dict = {}
            for octave in self.octaves:
                octaves[octave["name"]] = {}
                octaves[octave["name"]]["RF_outputs"] = {}
                octaves[octave["name"]]["RF_inputs"] = {}
                for rf_output in octave.get("rf_outputs", []):
                    octaves[octave["name"]]["RF_outputs"][rf_output["port"]] = {
                        "LO_frequency": rf_output["lo_frequency"],  # Should be between 2 and 18 GHz.
                        "LO_source": "internal",
                        "gain": rf_output["gain"] if "gain" in rf_output else 0.0,
                        "output_mode": "always_on",
                        "input_attenuators": "OFF",  # can be: "OFF" / "ON". Default is "OFF".
                    }
                    if "i_connection" in rf_output:
                        octaves[octave["name"]]["RF_outputs"][rf_output["port"]]["I_connection"] = (
                            (
                                rf_output["i_connection"]["controller"],
                                rf_output["i_connection"]["fem"],
                                rf_output["i_connection"]["port"],
                            )
                            if "fem" in rf_output["i_connection"]
                            else (rf_output["i_connection"]["controller"], rf_output["i_connection"]["port"])
                        )
                    if "q_connection" in rf_output:
                        octaves[octave["name"]]["RF_outputs"][rf_output["port"]]["Q_connection"] = (
                            (
                                rf_output["q_connection"]["controller"],
                                rf_output["q_connection"]["fem"],
                                rf_output["q_connection"]["port"],
                            )
                            if "fem" in rf_output["q_connection"]
                            else (rf_output["q_connection"]["controller"], rf_output["q_connection"]["port"])
                        )
                for rf_input in octave.get("rf_inputs", []):
                    octaves[octave["name"]]["RF_inputs"][rf_input["port"]] = {
                        "RF_source": "RF_in",
                        "LO_frequency": rf_input["lo_frequency"],
                        "LO_source": "internal",  # can be: "internal" / "external". Default is "internal".
                        "IF_mode_I": "direct",  # can be: "direct" / "mixer" / "envelope" / "off". Default is "direct".
                        "IF_mode_Q": "direct",
                    }
                if "loopbacks" in octave:
                    octaves[octave["name"]]["loopbacks"] = [
                        (
                            (octave["name"], octave["loopbacks"]["Synth"]),
                            octave["loopbacks"]["Dmd"],
                        )
                    ]
                if "connectivity" in octave:
                    octaves[octave["name"]]["connectivity"] = (
                        (octave["connectivity"]["controller"], octave["connectivity"]["fem"])
                        if "fem" in octave
                        else octave["connectivity"]["controller"]
                    )
                else:
                    octaves[octave["name"]]["IF_outputs"] = {
                        "IF_out1": {
                            "port": (
                                (
                                    octave["if_outputs"][0]["controller"],
                                    octave["if_outputs"][0]["fem"],
                                    octave["if_outputs"][0]["port"],
                                )
                                if "fem" in octave["if_outputs"][0]
                                else (octave["if_outputs"][0]["controller"], octave["if_outputs"][0]["port"])
                            ),
                            "name": "out1",
                        },
                        "IF_out2": {
                            "port": (
                                (
                                    octave["if_outputs"][1]["controller"],
                                    octave["if_outputs"][1]["fem"],
                                    octave["if_outputs"][1]["port"],
                                )
                                if "fem" in octave["if_outputs"][1]
                                else (octave["if_outputs"][1]["controller"], octave["if_outputs"][1]["port"])
                            ),
                            "name": "out2",
                        },
                    }
            return octaves

        def _get_elements_and_mixers_config(self) -> tuple:
            """Returns the elements config dictionary.

            Returns:
                elements: Dict[str, Any]
            """
            elements = {}
            mixers = {}

            for element in self.elements:
                bus_name = str(element["identifier"])
                element_dict: dict = {"operations": {}}

                # Flux bus
                if "single_input" in element:
                    intermediate_frequency = (
                        int(element["intermediate_frequency"]) if "intermediate_frequency" in element else 0
                    )
                    element_dict["singleInput"] = {
                        "port": (
                            (
                                element["single_input"]["controller"],
                                element["single_input"]["fem"],
                                element["single_input"]["port"],
                            )
                            if "fem" in element["single_input"]
                            else (element["single_input"]["controller"], element["single_input"]["port"])
                        ),
                    }
                    element_dict["intermediate_frequency"] = intermediate_frequency
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
                        key: (
                            (
                                element["mix_inputs"][key]["controller"],
                                element["mix_inputs"][key]["fem"],
                                element["mix_inputs"][key]["port"],
                            )
                            if "fem" in element["mix_inputs"][key]
                            else (element["mix_inputs"][key]["controller"], element["mix_inputs"][key]["port"])
                        )
                        for key in ["I", "Q"]
                    } | {"lo_frequency": lo_frequency, "mixer": mixer_name}
                    element_dict["intermediate_frequency"] = intermediate_frequency

                    # readout bus
                    if "outputs" in element:
                        element_dict["outputs"] = {
                            key: (
                                (
                                    element["outputs"][key]["controller"],
                                    element["outputs"][key]["fem"],
                                    element["outputs"][key]["port"],
                                )
                                if "fem" in element["outputs"][key]
                                else (element["outputs"][key]["controller"], element["outputs"][key]["port"])
                            )
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
                            "port": (
                                (
                                    element["digital_inputs"]["controller"],
                                    element["digital_inputs"]["fem"],
                                    element["digital_inputs"]["port"],
                                )
                                if "fem" in element["digital_inputs"]
                                else (element["digital_inputs"]["controller"], element["digital_inputs"]["port"])
                            ),
                            "delay": element["digital_inputs"]["delay"],
                            "buffer": element["digital_inputs"]["buffer"],
                        }
                    }
                if "digital_outputs" in element:
                    element_dict["digitalOutputs"] = {
                        "port": (
                            (
                                element["digital_outputs"]["controller"],
                                element["digital_outputs"]["fem"],
                                element["digital_outputs"]["port"],
                            )
                            if "fem" in element["digital_outputs"]
                            else (element["digital_outputs"]["controller"], element["digital_outputs"]["port"])
                        ),
                    }

                elements[bus_name] = element_dict

            return elements, mixers

    settings: QuantumMachinesClusterSettings
    device: QMMDriver
    _qmm: QuantumMachinesManager
    _qm: QuantumMachine  # TODO: Change private QM API to public when implemented.
    _config: DictQuaConfig
    _octave_config: QmOctaveConfig | None = None
    _is_connected_to_qm: bool = False
    _config_created: bool = False
    _pending_set_intermediate_frequency: dict[str, float] = {}  # noqa: RUF012
    _compiled_program_cache: dict[str, str] = {}  # noqa: RUF012

    @property
    def config(self) -> DictQuaConfig:
        """Get the QUA config dictionary."""
        return self._config

    def is_awg(self) -> bool:
        """Returns True if instrument is an AWG."""
        return True

    def is_adc(self) -> bool:
        """Returns True if instrument is an ADC."""
        return True

    @check_device_initialized
    def initial_setup(self):
        """Sets initial instrument settings.

        Creates an instance of the Qililab Quantum Machines Manager, and sets the configuration dictionary.
        """
        if self.settings.octaves:
            self._octave_config = QmOctaveConfig()
            self._octave_config.set_calibration_db(os.getcwd())

        self._qmm = (
            QuantumMachinesManager(
                host=self.settings.address,
                cluster_name=self.settings.cluster,
                octave_calibration_db_path=self._octave_config._calibration_db_path,
            )
            if self._octave_config is not None
            else QuantumMachinesManager(
                host=self.settings.address,
                cluster_name=self.settings.cluster,
            )
        )
        self._config = self.settings.to_qua_config()
        self._config_created = True

    @check_device_initialized
    def turn_on(self):
        """Turns on the instrument."""
        if not self._is_connected_to_qm:
            self._qm = self._qmm.open_qm(config=self._config, close_other_machines=True)
            self._compiled_program_cache = {}
            self._is_connected_to_qm = True

            if self.settings.run_octave_calibration:
                self.run_octave_calibration()

    @check_device_initialized
    def reset(self):
        """Resets instrument settings."""

    @check_device_initialized
    def turn_off(self):
        """Turns off an instrument."""
        if self._is_connected_to_qm:
            self._qm.close()
            self._is_connected_to_qm = False

    def append_configuration(self, configuration: dict):
        """Update the `_config` dictionary by appending the configuration generated by compilation.

        Args:
            configuration (dict): Configuration dictionary to append to the existing configuration.

        Raises:
            ValueError: Raised if the `_config` dictionary does not exist.
        """
        if not self._config_created:
            raise ValueError("The QM `config` dictionary does not exist. Please run `initial_setup()` first.")

        merged_configuration = merge_dictionaries(dict(self._config), configuration)
        if self._config != merged_configuration:
            self._config = cast("DictQuaConfig", merged_configuration)
            # If we are already connected, reopen the connection with the new configuration
            if self._is_connected_to_qm:
                self._qm.close()
                self._qm = self._qmm.open_qm(config=self._config, close_other_machines=True)  # type: ignore[assignment]
                self._compiled_program_cache = {}

    def run_octave_calibration(self):
        """Run calibration procedure for the buses with octaves, if any."""
        elements = [element for element in self._config["elements"] if "RF_inputs" in self._config["elements"][element]]
        for element in elements:
            self._qm.calibrate_element(element)

    def get_controller_type_from_bus(self, bus: str) -> str | None:
        """Gets the OPX controller name of the bus used

        Args:
            bus (str): Alias of the bus

        Raises:
            AttributeError: Raised when given bus does not exist

        Returns:
            str | None: Alias of the controller, either opx1 or opx1000.
        """

        if "RF_inputs" in self._config["elements"][bus]:
            octave = self._config["elements"][bus]["RF_inputs"]["port"][0]
            controller_name = self._config["octaves"][octave]["connectivity"]
        elif "mixInputs" in self._config["elements"][bus]:
            controller_name = self._config["elements"][bus]["mixInputs"]["I"][0]
        elif "singleInput" in self._config["elements"][bus]:
            controller_name = self._config["elements"][bus]["singleInput"]["port"][0]

        for controller in self.settings.controllers:
            if controller["name"] == controller_name:
                return controller["type"] if "type" in controller else "opx1"
        raise AttributeError(f"Controller with bus {bus} does not exist")

    def get_controller_from_element(self, element: dict, key: str | None) -> tuple[str, int, int | None]:
        """Get controller name, port and FEM (if applicable) from element

        Args:
            element (dict): element of a bus
            key (str | None): Key for mix inputs, it can be I or Q.

        Returns:
            list: controller coordinates
        """
        if ("rf_inputs" in element or "mix_inputs" in element) and key not in ["I", "Q"]:
            raise ValueError(f"key value must be I or Q, {key} given")
        if "rf_inputs" in element:
            octave_name = element["rf_inputs"]["octave"]
            out_oct_port = element["rf_inputs"]["port"]

            octave = next((octave for octave in self.settings.octaves if octave["name"] == octave_name), None)
            octave_port = (
                next(
                    (octave_port for octave_port in octave["rf_outputs"] if octave_port["port"] == out_oct_port),
                    None,
                )
                if octave
                else None
            )

            connection = "i_connection" if key == "I" else "q_connection"
            if connection in octave_port:  # type: ignore[operator]
                con_name = octave_port[connection]["controller"]  # type: ignore[index]
                con_port = octave_port[connection]["port"]  # type: ignore[index]
                con_fem = octave_port[connection]["fem"] if "fem" in octave_port[connection] else None  # type: ignore[index]
            else:
                con_name = octave["connectivity"]["controller"]  # type: ignore[index]
                con_port = octave_port["port"] * 2 - 1 if key == "I" else octave_port["port"] * 2  # type: ignore[index]
                con_fem = None

        elif "mix_inputs" in element:
            con_name = element["mix_inputs"][key]["controller"]
            con_port = element["mix_inputs"][key]["port"]
            con_fem = element["mix_inputs"][key]["fem"] if "fem" in element["mix_inputs"][key] else None

        elif "single_input" in element:
            con_name = element["single_input"]["controller"]
            con_port = element["single_input"]["port"]
            con_fem = element["single_input"]["fem"] if "fem" in element["single_input"] else None

        return (con_name, con_port, con_fem)

    @log_set_parameter
    def set_parameter(
        self,
        parameter: Parameter,
        value: ParameterValue,
        channel_id: ChannelID | None = None,
        output_id: OutputID | None = None,
    ) -> None:
        """Sets the parameter of the instrument into the cache (runtime dataclasses).

        And if connection to instruments is established, then to the instruments as well.

        Args:
            bus (str): The assossiated bus to change parameter.
            parameter (Parameter): The parameter to update.
            value (float | str | bool): The new value of the parameter.

        Raises:
            ValueError: Raised when passed bus is not found, or rf_inputs is not connected to an octave.
            ParameterNotFound: Raised if parameter does not exist.
        """
        bus = str(channel_id)
        element = next((element for element in self.settings.elements if element["identifier"] == bus), None)
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

        # Now we will set the parameter in 3 places:
        # 1) In the settings runtime dataclass (always).
        # 2) If created: In the `_config`` dictionary.
        # 3) If connected: In the instrument itself.
        if parameter == Parameter.LO_FREQUENCY:
            lo_frequency = float(value)
            settings_octave_rf_output["lo_frequency"] = lo_frequency
            if self._config_created:
                self._config["octaves"][octave_name]["RF_outputs"][out_port]["LO_frequency"] = lo_frequency
            if self._is_connected_to_qm:
                self._qm.octave.set_lo_frequency(element=bus, lo_frequency=lo_frequency)
                self._qm.calibrate_element(bus)
            if in_port is not None:
                settings_octave_rf_input = next(
                    rf_input for rf_input in settings_octave["rf_inputs"] if rf_input["port"] == in_port
                )
                settings_octave_rf_input["lo_frequency"] = lo_frequency
                if self._config_created:
                    self._config["octaves"][octave_name]["RF_inputs"][in_port]["LO_frequency"] = lo_frequency
            return

        if parameter == Parameter.GAIN:
            gain_in_db = float(value)
            settings_octave_rf_output["gain"] = gain_in_db
            if self._config_created:
                self._config["octaves"][octave_name]["RF_outputs"][out_port]["gain"] = gain_in_db
            if self._is_connected_to_qm:
                self._qm.octave.set_rf_output_gain(element=bus, gain_in_db=gain_in_db)
            return

        if parameter == Parameter.IF:
            intermediate_frequency = float(value)
            element["intermediate_frequency"] = intermediate_frequency
            if self._config_created:
                self._config["elements"][bus]["intermediate_frequency"] = intermediate_frequency
                if f"mixer_{bus}" in self._config["mixers"]:
                    self._config["mixers"][f"mixer_{bus}"][0]["intermediate_frequency"] = intermediate_frequency
            if self._is_connected_to_qm:
                controller_type = self.get_controller_type_from_bus(bus)
                if controller_type == "opx1":
                    self._qm.set_intermediate_frequency(element=bus, freq=intermediate_frequency)
                if controller_type == "opx1000":
                    self._pending_set_intermediate_frequency[bus] = intermediate_frequency
            return

        if parameter == Parameter.THRESHOLD_ROTATION:
            threshold_rotation = float(value)
            element["threshold_rotation"] = threshold_rotation
            return

        if parameter == Parameter.THRESHOLD:
            threshold = float(value)
            element["threshold"] = threshold
            return

        if parameter == Parameter.DC_OFFSET:
            con_name, con_port, con_fem = self.get_controller_from_element(element=element, key=None)
            dc_offset = float(value)
            settings_controllers = next(
                controller for controller in self.settings.controllers if controller["name"] == con_name
            )
            if con_fem is None:
                settings_offset = next(
                    analog_output
                    for analog_output in settings_controllers["analog_outputs"]
                    if analog_output["port"] == con_port
                )
            else:
                settings_fem = next(fem for fem in settings_controllers["fems"] if fem["fem"] == con_fem)
                settings_offset = next(
                    analog_output
                    for analog_output in settings_fem["analog_outputs"]
                    if analog_output["port"] == con_port
                )
            settings_offset["offset"] = dc_offset
            if self._config_created:
                if con_fem is None:
                    self._config["controllers"][con_name]["analog_outputs"][con_port]["offset"] = dc_offset  # type: ignore[typeddict-item]
                else:
                    self._config["controllers"][con_name]["fems"][con_fem]["analog_outputs"][con_port][  # type: ignore[typeddict-item, index]
                        "offset"  # type: ignore[typeddict-unknown-key]
                    ] = dc_offset
            if self._is_connected_to_qm:
                self._qm.set_output_dc_offset_by_element(element=bus, input="single", offset=dc_offset)
            return

        if parameter in [Parameter.OFFSET_I, Parameter.OFFSET_Q]:
            key = "I" if parameter == Parameter.OFFSET_I else "Q"
            con_name, con_port, con_fem = self.get_controller_from_element(element=element, key=key)
            input_offset = float(value)
            settings_controllers = next(
                controller for controller in self.settings.controllers if controller["name"] == con_name
            )
            if con_fem is None:
                settings_offset = next(
                    analog_output
                    for analog_output in settings_controllers["analog_outputs"]
                    if analog_output["port"] == con_port
                )
            else:
                settings_fem = next(fem for fem in settings_controllers["fems"] if fem["fem"] == con_fem)
                settings_offset = next(
                    analog_output
                    for analog_output in settings_fem["analog_outputs"]
                    if analog_output["port"] == con_port
                )
            settings_offset["offset"] = input_offset
            if self._config_created:
                if con_fem is None:
                    self._config["controllers"][con_name]["analog_outputs"][con_port]["offset"] = input_offset  # type: ignore[typeddict-item]
                else:
                    self._config["controllers"][con_name]["fems"][con_fem]["analog_outputs"][con_port][  # type: ignore[typeddict-item, index]
                        "offset"  # type: ignore[typeddict-unknown-key]
                    ] = input_offset
            if self._is_connected_to_qm:
                self._qm.set_output_dc_offset_by_element(element=bus, input=key, offset=input_offset)
            return

        if parameter in [Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2]:
            output = "out1" if parameter == Parameter.OFFSET_OUT1 else "out2"
            out_value = 1 if output == "out1" else 2
            con_name, _, con_fem = self.get_controller_from_element(element=element, key="I")
            output_offset = float(value)
            settings_controllers = next(
                controller for controller in self.settings.controllers if controller["name"] == con_name
            )
            if con_fem is None:
                settings_offset = next(
                    analog_output
                    for analog_output in settings_controllers["analog_inputs"]
                    if analog_output["port"] == out_value
                )
            else:
                settings_fem = next(fem for fem in settings_controllers["fems"] if fem["fem"] == con_fem)
                settings_offset = next(
                    analog_output
                    for analog_output in settings_fem["analog_inputs"]
                    if analog_output["port"] == out_value
                )
            settings_offset["offset"] = output_offset
            if self._config_created:
                if con_fem is None:
                    self._config["controllers"][con_name]["analog_inputs"][out_value]["offset"] = output_offset  # type: ignore[typeddict-item]
                else:
                    self._config["controllers"][con_name]["fems"][con_fem]["analog_inputs"][out_value][  # type: ignore[typeddict-item, index]
                        "offset"  # type: ignore[typeddict-unknown-key]
                    ] = output_offset
            if self._is_connected_to_qm:
                self._qm.set_input_dc_offset_by_element(element=bus, output=output, offset=output_offset)
            return

        raise ParameterNotFound(self, parameter)

    def get_parameter(
        self, parameter: Parameter, channel_id: ChannelID | None = None, output_id: OutputID | None = None
    ) -> ParameterValue:
        """Gets the value of a parameter.

        Args:
            bus (str): The associated bus of the parameter.
            parameter (Parameter): The parameter to get value.

        Returns:
            float | int | bool | tuple: The value of the parameter.

        Raises:
            ParameterNotFound: Raised if parameter does not exist.
        """
        # Just in case, read from the `settings`, even though in theory the config should always be synch:
        bus = str(channel_id)
        settings_config_dict = self.settings.to_qua_config()
        config_keys = settings_config_dict["elements"][bus]
        element = next((element for element in self.settings.elements if element["identifier"] == bus), None)

        if parameter == Parameter.LO_FREQUENCY:
            if "mixInputs" in config_keys:
                return settings_config_dict["elements"][bus]["mixInputs"]["lo_frequency"]
            if "RF_inputs" in config_keys:
                port = settings_config_dict["elements"][bus]["RF_inputs"]["port"]
                return settings_config_dict["octaves"][port[0]]["RF_outputs"][port[1]]["LO_frequency"]

        if parameter == Parameter.IF:
            if "intermediate_frequency" in config_keys:
                return settings_config_dict["elements"][bus]["intermediate_frequency"]

        if parameter == Parameter.GAIN:
            if "mixInputs" in config_keys and "outputs" in config_keys:
                port_i = settings_config_dict["elements"][bus]["outputs"]["out1"]
                # port_q = settings_config_dict["elements"][bus]["outputs"]["out2"]
                return settings_config_dict["controllers"][port_i[0]]["analog_inputs"][port_i[1]]["gain_db"]  # type: ignore[typeddict-item]
                # return (
                #     settings_config_dict["controllers"][port_i[0]]["analog_inputs"][port_i[1]]["gain_db"],  # type: ignore[typeddict-item]
                #     settings_config_dict["controllers"][port_q[0]]["analog_inputs"][port_q[1]]["gain_db"],  # type: ignore[typeddict-item]
                # )
            if "RF_inputs" in config_keys:
                port = settings_config_dict["elements"][bus]["RF_inputs"]["port"]
                return settings_config_dict["octaves"][port[0]]["RF_outputs"][port[1]]["gain"]

        if parameter == Parameter.TIME_OF_FLIGHT:
            if "time_of_flight" in config_keys:
                return settings_config_dict["elements"][bus]["time_of_flight"]

        if parameter == Parameter.SMEARING:
            if "smearing" in config_keys:
                return settings_config_dict["elements"][bus]["smearing"]

        if parameter in [Parameter.THRESHOLD_ROTATION, Parameter.THRESHOLD]:
            element = next((element for element in self.settings.elements if element["identifier"] == bus), None)
            if parameter == Parameter.THRESHOLD_ROTATION:
                return element.get("threshold_rotation", None)  # type: ignore
            if parameter == Parameter.THRESHOLD:
                return element.get("threshold", None)  # type: ignore

        if parameter == Parameter.DC_OFFSET:
            con_name, con_port, con_fem = self.get_controller_from_element(element=element, key=None)  # type: ignore[arg-type]
            if con_fem is None:
                return settings_config_dict["controllers"][con_name]["analog_outputs"][con_port]["offset"]  # type: ignore[typeddict-item]
            return settings_config_dict["controllers"][con_name]["fems"][con_fem]["analog_outputs"][con_port]["offset"]  # type: ignore[typeddict-item, index]

        if parameter in [Parameter.OFFSET_I, Parameter.OFFSET_Q]:
            key = "I" if parameter in Parameter.OFFSET_I else "Q"
            con_name, con_port, con_fem = self.get_controller_from_element(element=element, key=key)  # type: ignore[arg-type]
            if con_fem is None:
                return settings_config_dict["controllers"][con_name]["analog_outputs"][con_port]["offset"]  # type: ignore[typeddict-item]
            return settings_config_dict["controllers"][con_name]["fems"][con_fem]["analog_outputs"][con_port]["offset"]  # type: ignore[typeddict-item, index]

        if parameter in [Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2]:
            output = "out1" if parameter in Parameter.OFFSET_OUT1 else "out2"
            out_value = 1 if output == "out1" else 2
            con_name, _, con_fem = self.get_controller_from_element(element=element, key="I")  # type: ignore[arg-type]
            if con_fem is None:
                return settings_config_dict["controllers"][con_name]["analog_inputs"][out_value]["offset"]  # type: ignore[typeddict-item]
            return settings_config_dict["controllers"][con_name]["fems"][con_fem]["analog_inputs"][out_value]["offset"]  # type: ignore[typeddict-item, index]

        raise ParameterNotFound(self, parameter)

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

    def run_compiled_program(self, compiled_program_id: str) -> QmJob | JobApi:
        """Executes a previously compiled QUA program identified by its unique compiled program ID.

        This method submits the compiled program to the Quantum Machines (QM) execution queue and waits for
        its execution to complete. The execution of the program is managed by the QM's queuing system,
        which schedules and runs the job on the quantum hardware or simulator as per availability and queue status.

        Args:
            compiled_program_id (str): The unique identifier of the compiled QUA program to be executed. This ID should correspond to a program that has already been compiled and is present in the program cache.

        Returns:
            RunningQmJob: An object representing the running job. This object provides methods and properties to check the status of the job, retrieve results upon completion, and manage or investigate the job's execution.
        """
        # TODO: qm.queue.add_compiled() -> qm.add_compiled()
        pending_job = self._qm.queue.add_compiled(compiled_program_id)

        # TODO: job.wait_for_execution() is deprecated and will be removed in the future. Please use job.wait_until("Running") instead.
        job = pending_job.wait_for_execution()  # type: ignore[return-value, union-attr]
        if self._pending_set_intermediate_frequency:
            for bus, intermediate_frequency in self._pending_set_intermediate_frequency.items():
                job.set_intermediate_frequency(element=bus, freq=intermediate_frequency)  # type: ignore[union-attr]
                self._qm.calibrate_element(bus)
            self._pending_set_intermediate_frequency = {}

        return job

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

    def get_acquisitions(self, job: QmJob | JobApi) -> dict[str, np.ndarray]:
        """Fetches the results from the execution of a QUA Program.

        Once the results have been fetched, they are returned wrapped in a QuantumMachinesResult instance.

        Args:
            job (QmJob): Job that provides the result handles.

        Returns:
            QuantumMachinesResult: Quantum Machines result instance.
        """
        result_handles_fetchers = job.result_handles
        result_handles_fetchers.wait_for_all_values(timeout=self.settings.timeout)
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
