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
import numpy as np
from typing import Dict
from qm import SimulationConfig
from qm.qua import Program
from qm import QuantumMachine, QuantumMachinesManager
from qililab.constants import RUNCARD
from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.result import Result
from qililab.typings import InstrumentName, QMMDriver

@InstrumentFactory.register
class QMM(Instrument):
    """Class defining the Qililab Quantum Machines Manager."""

    name = InstrumentName.QMM

    @dataclass
    class QMMSettings(Instrument.InstrumentSettings):
        """Settings for Quantum Machines Manager instrument."""

        qop_ip: str
        qop_port: int
        config: Dict

    settings: QMMSettings
    device: QMMDriver
    qm: QuantumMachine

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Set initial instrument settings."""
        super().initial_setup()
        qmm = QuantumMachinesManager(host=self.settings.qop_ip, port=self.settings.qop_port)
        self.qm = qmm.open_qm(self.settings.config)

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Turn on an instrument."""

    @Instrument.CheckDeviceInitialized   
    def reset(self):
        """Reset instrument settings."""

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Turn off an instrument."""

    def run(self, program:Program) -> Result:
        """Run the QUA Program"""
        job = self.qm.execute(program)
        res_handles = job.result_handles
        res_handles.wait_for_all_values()

        return res_handles

    def simulate(self, program:Program) -> Result:
        """Run the QProgram"""
        job = self.qm.simulate(program, SimulationConfig(40_000))
        return job.result_handles


    def to_dict(self):
        """Return a dict representation of an OPX instrument."""
        return {RUNCARD.NAME: self.name.value} | self.settings.to_dict()
