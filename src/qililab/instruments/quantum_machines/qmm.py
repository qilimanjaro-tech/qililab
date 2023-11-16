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

from qm import QuantumMachine
from qm import QuantumMachinesManager as QMM
from qm import SimulationConfig
from qm.jobs.running_qm_job import RunningQmJob
from qm.qua import Program

from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.result.quantum_machines_results import QuantumMachinesResult
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
            address (str): I.P. address to connect to the Quantum Machines instruments.
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
        self.config = self.create_config()
        qmm = QMM(host=self.settings.address, port=self.settings.port)
        self.qm = qmm.open_qm(config=self.settings.config, close_other_machines=True)

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

    def create_config(self) -> Dict[str, Any]:
        """Creates the Quantum Machines config dictionary.

        Creates, an instance of a dictionary in the format that QuantumMachines expects the config dictionary to be.
        Controllers (instruments in the quantum machines stack) and elements (buses) are parsed from the QMMSettings
        object of this class to generate the right output that will be added to the config dictionary generated out of the
        QProgram compiler.

        Returns:
            config: Dict[str, Any]
        """
        config = {
            "version": 1,  # hardcoded for now, need to check what version really refers to
            "controllers": self._get_controllers_config(),
            "elements": self._get_elements_config(),
            "octaves": self._get_octaves_config(),
        }

        return config

    def _get_controllers_config(self) -> dict[str, Any]:
        """Returns the controllers config dictionary.

        Returns:
            controllers: Dict[str, Any]
        """
        controllers = {}
        for controller in self.settings.controllers:
            controllers[controller["name"]] = {
                "analog_outputs": [
                    {output["port"]: {"offset": output["offset"]}} for output in controller.get("analog_outputs", [])
                ],
                "analog_inputs": [
                    {input["port"]: {"offset": input["offset"], "gain_db": input["gain_db"]}} for input in controller.get("analog_inputs", [])
                ],
                "digital_outputs": [
                    {output["port"]: {}} for output in controller.get("digital_outputs", [])
                ]
            }

        return controllers

    def _get_elements_config(self) -> dict[str, Any]:
        """Returns the elements config dictionary.

        Returns:
            elements: Dict[str, Any]
        """
        elements = {}

        for element in self.settings.elements:
            if "rf_bus" in element["bus"]:
                bus_dict = {
                    "rf_inputs": {
                        "octave": element["rf_inputs"]["octave"],
                        "port": element["rf_inputs"]["port"],
                    },
                    "rf_outputs": {
                        "octave": element["rf_outputs"]["octave"],
                        "port": element["rf_outputs"]["port"],
                    },
                    "digital_inputs": {
                        "controller": element["digital_inputs"]["controller"],
                        "port": element["digital_inputs"]["port"],
                        "delay": element["digital_inputs"]["delay"],
                        "buffer": element["digital_inputs"]["buffer"],
                    },
                    "intermediate_frequency": element["intermediate_frequency"]
                }
            elif "flux" in element["bus"]:
                bus_dict = {
                    "singleInput": {
                        "controller": element["singleInput"]["controller"],
                        "port": element["singleInput"]["port"],
                    }
                }
            else:
                bus_dict = {
                    "mixInputs": {
                        key: (element["mixInputs"][key]["controller"], element["mixInputs"][key]["port"])
                        for key in ["I", "Q"]
                    },
                    "lo_frequency": element["mixInputs"]["lo_frequency"],
                    "mixer_correction": element["mixInputs"]["mixer_correction"],
                    "intermediate_frequency": element["intermediate_frequency"]
                }

            elements[element["bus"]] = bus_dict

        return elements

    def _get_octaves_config(self) -> dict[str, Any]:
        """Returns the octaves config dictionary.

        Returns:
            octaves: Dict[str, Any]
        """
        octaves = {}

        for octave in self.settings.octaves:
            octaves[octave["name"]] = {
                "port": octave["port"],
                "controller": octave["controller"],
                "rf_outputs": [
                    {output["port"]: {"lo_frequency": output["lo_frequency"], "gain": output["gain"]}} for output in octave.get("rf_outputs", [])
                ],
            }

        return octaves

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

    def get_acquisitions(self, job: RunningQmJob) -> QuantumMachinesResult:
        """Fetches the results from the execution of a QUA Program.

        Once the results have been fetched, they are returned wrapped in a QuantumMachinesResult instance.

        Args:
            job (QmJob): Job that provides the result handles.

        Returns:
            QuantumMachinesResult: Quantum Machines result instance.
        """
        result_handles_fetchers = job.result_handles
        result_handles_fetchers.wait_for_all_values()
        # TODO: we might need to use 'name' in 'name, handle in job.result_handles' in the future
        results = [handle.fetch_all() for _, handle in job.result_handles if handle is not None]

        return QuantumMachinesResult(raw_results=results)

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
