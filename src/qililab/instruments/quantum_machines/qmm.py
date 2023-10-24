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

"""Quantum Machines OPX class."""
from dataclasses import dataclass
from typing import Dict

from qm import QuantumMachine, QuantumMachinesManager, SimulationConfig
from qm.qua import Program

from qililab.constants import RUNCARD
from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.result.quantum_machines_results import QuantumMachinesResult
from qililab.typings import InstrumentName, QMMDriver


@InstrumentFactory.register
class QMM(Instrument):
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

    name = InstrumentName.QMM

    @dataclass
    class QMMSettings(Instrument.InstrumentSettings):
        """Settings for Quantum Machines Manager instrument.

        Args:
            qop_ip (str): I.P. address to connect to the Quantum Machines instruments.
            qop_port (int): Port to connect to the Quantum Machines instruments.
            config (Dict): Configuration dictionary for the Quantum Machines instruments.
        """

        qop_ip: str
        qop_port: int
        config: Dict

    settings: QMMSettings
    device: QMMDriver
    qmm: QuantumMachinesManager

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Sets initial instrument settings.

        Creates an instance of the Qilililab Quantum Machines Manager, and the Quantum Machine, opening
        a connection to the Quantum Machine by the use of the Quantum Machines Manager.
        """
        super().initial_setup()
        self.qmm = QuantumMachinesManager(host=self.settings.qop_ip, port=self.settings.qop_port)

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Turns on an instrument."""

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Resets instrument settings."""

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Turns off an instrument."""

    def run(self, program: Program) -> QuantumMachinesResult:
        """Runs the QUA Program.

        Creates, for every execution, an instance of a QuantumMachine class and executes the QUA program on it.
        After execution, the results are fetched through the fetcher tool from the qm library.

        Args:
            program (Program): QUA Program to be run on Quantum Machines instruments.
        """
        qm = self.qmm.open_qm(self.settings.config)
        job = qm.execute(program)
        res_handles = job.result_handles
        res_handles.wait_for_all_values()
        res_handles.fetch_all()

        return QuantumMachinesResult(raw_results=res_handles)

    def simulate(self, program: Program) -> QuantumMachinesResult:
        """Simulates the QUA Program.

        Creates, for every simulation, an instance of a QuantumMachine class and executes the QUA program on it.
        After simulation, the results are fetched through the fetcher tool from the qm library.

        Args:
            program (Program): QUA Program to be simulated on Quantum Machines instruments.
        """
        qm = self.qmm.open_qm(self.settings.config)
        job = qm.simulate(program, SimulationConfig(40_000))
        res_handles = job.result_handles

        return QuantumMachinesResult(raw_results=res_handles.fetch_all())

    def to_dict(self):
        """Returns a dict representation of a Quantum Machines Manager instrument.

        Returns:
            dict[str: str | dict]: Dictionary containing the runcard name and the instrument settings.
        """
        return {RUNCARD.NAME: self.name.value} | self.settings.to_dict()
