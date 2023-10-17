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
from typing import Any, Dict
from qm.QuantumMachinesManager import QuantumMachinesManager
from qililab.constants import RUNCARD
from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.qprogram import QProgram
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

    def __init__(self, settings: dict):
        # It creates a new instance of the Quantum Machines Manager
        self.qmm = QuantumMachinesManager(host=self.settings.qop_ip, port=self.settings.qop_port)
        self.qm = self.qmm.open_qm(self.settings.config)

        super().__init__(settings=settings)

    def run(self, program:QProgram) -> Any:
        """Run the QProgram"""
        job = self.qm.execute(program)
        res_handles = job.result_handles
        res_handles.wait_for_all_values()

    def to_dict(self):
        """Return a dict representation of an OPX instrument."""
        return {RUNCARD.NAME: self.name.value} | self.settings.to_dict()
