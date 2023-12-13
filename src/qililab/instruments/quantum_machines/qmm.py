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
from dataclasses import dataclass
from typing import Any, Dict

import numpy as np
from qm import QuantumMachine
from qm import QuantumMachinesManager as QMM
from qm import SimulationConfig
from qm.jobs.running_qm_job import RunningQmJob
from qm.qua import Program

from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName, Parameter, QMMDriver


@InstrumentFactory.register
class QuantumMachinesManager(Instrument):
    """Class defining the Qililab Quantum Machines Manager instrument in Qililab.

    This class allows Qililab control and communication with an instance of the
    Quantum Machines Manager, which is the central class to interact with Quantum Machines instruments.
    The manager is responsible, through the use of QUA sequences, of setting the Quantum Machines instruments
    in the right manner for Quantum Control.

    Args:
        name (InstrumentName): Name of the Instrument.
        device (QMMDriver): Instance of the Quantum Machines Manager Driver class.
        settings (QMMSettings): Settings of the instrument.
    """

    name = InstrumentName.QUANTUM_MACHINES_MANAGER

    @dataclass
    class QMMSettings(Instrument.InstrumentSettings):
        """Settings for Quantum Machines Manager instrument.

        Args:
            address (str): IP address to connect to the Quantum Machines instruments.
            port (int): Port to connect to the Quantum Machines instruments.
            num_controllers (int): Number of controllers (instruments) in the quantum machines stack.
            octaves (list[dict[str, Any]]): List of octaves the quantum machines stack has.
            controllers (list[dict[str, Any]]): List of controllers (instruments) the quantum machines stack has.
            elements (list[dict[str, Any]]): List of elements (buses) the quantum machines stack has.
        """

        address: str
        port: int
        octaves: list[dict[str, Any]]
        controllers: list[dict[str, Any]]
        elements: list[dict[str, Any]]

        def to_qua_config(self) -> Dict[str, Any]:
            """Creates the Quantum Machines config dictionary.

            Creates, an instance of a dictionary in the format that QuantumMachines expects the config dictionary to be.
            Controllers (instruments in the quantum machines stack) and elements (buses) are parsed from the QMMSettings
            object of this class to generate the right output that will be added to the config dictionary generated out of the
            QProgram compiler.

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
                        output["port"]: {"offset": output["offset"], "delay": output["delay"]}
                        for output in controller.get("analog_outputs", [])
                    },
                    "analog_inputs": {
                        input["port"]: {"offset": input["offset"], "gain_db": input["gain"]}
                        for input in controller.get("analog_inputs", [])
                    },
                    "digital_outputs": {output["port"]: {} for output in controller.get("digital_outputs", [])},
                }
                for controller in self.controllers
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
                    mixers[mixer_name] = [
                        {
                            "intermediate_frequency": intermediate_frequency,
                            "lo_frequency": lo_frequency,
                            "correction": element["mix_inputs"]["mixer_correction"],
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
                        "port": (element["digital_inputs"]["controller"], element["digital_inputs"]["port"]),
                        "delay": element["digital_inputs"]["delay"],
                        "buffer": element["digital_inputs"]["buffer"],
                    }
                if "digital_outputs" in element:
                    element_dict["digitalOutputs"] = {
                        "port": (element["digital_outputs"]["controller"], element["digital_outputs"]["port"]),
                    }

                elements[bus_name] = element_dict

            return elements, mixers

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
                            "gain": output["gain"],
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
                    "connectivity": octave["connected_to"],
                }
                for octave in self.octaves
            }

    settings: QMMSettings
    device: QMMDriver
    qm: QuantumMachine
    config: dict | None = None

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Sets initial instrument settings.

        Creates an instance of the Qilililab Quantum Machines Manager, and the Quantum Machine, opening
        a connection to the Quantum Machine by the use of the Quantum Machines Manager.
        """
        super().initial_setup()
        self.config = self.settings.to_qua_config()
        qmm = QMM(host=self.settings.address, port=self.settings.port)
        self.qm = qmm.open_qm(config=self.config, close_other_machines=True)

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Turns on an instrument."""

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Resets instrument settings."""

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Turns off an instrument."""

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Sets the parameter of a specific instrument.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.

        Returns:
            bool: True if the parameter is set correctly, False otherwise
        """
        raise NotImplementedError("Setting a parameter is not supported for Quantum Machines yet.")

    def run(self, program: Program) -> RunningQmJob:
        """Runs the QUA Program.

        Creates, for every execution, an instance of a QuantumMachine class and executes the QUA program on it.
        After execution, the job generated by the Quantum Machines Manager is returned.

        Args:
            program (Program): QUA Program to be run on Quantum Machines instruments.

        Returns:
            job: Quantum Machines job.
        """

        return self.qm.execute(program)

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
        return self.qm.simulate(program, SimulationConfig(40_000))
