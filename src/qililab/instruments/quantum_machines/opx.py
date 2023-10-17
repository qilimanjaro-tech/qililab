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
from qililab.constants import RUNCARD
from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.qprogram import QProgram
from qililab.typings import InstrumentName, OPXDriver

@InstrumentFactory.register
class OPX(Instrument):
    """Class defining the Qililab OPX wrapper for Quantum Machines OPX Driver."""

    name = InstrumentName.OPX

    @dataclass
    class OPXSettings(Instrument.InstrumentSettings):
        """Settings for Quantum Machines OPX instrument."""

        config: Dict
        name: str
        host: str
        port: str
        cluster_name: str
        octave: Any
        close_other_machines: bool = True

    settings: OPXSettings
    device: OPXDriver

    def execute(self, program:QProgram):
        """Run the uploaded program"""
        self.device.execute(program=program)

    def to_dict(self):
        """Return a dict representation of an OPX instrument."""
        return {RUNCARD.NAME: self.name.value} | self.settings.to_dict()
