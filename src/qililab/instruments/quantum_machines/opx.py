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
import numpy as np
from typing import Dict
from qililab.constants import RUNCARD
from qililab.instruments.utils import InstrumentFactory
from qualang_tools.external_frameworks.qcodes.opx_driver import OPX as QuantumMachinesOPX

@InstrumentFactory.register
class OPX(QuantumMachinesOPX):
    """Class defining the Qililab OPX wrapper for Quantum Machines OPX Driver."""

    def __init__(self,
                 config: Dict,
                 name: str,
                 host: str,
                 port: str,
                 cluster_name: str,
                 octave,
                 close_other_machines: bool = True):
        """Initialise the instrument.

        Args:
            parent (Instrument): Parent for the sequencer instance.
            name (str): Sequencer name
            seq_idx (int): sequencer identifier index
            sequence_timeout (int): timeout to retrieve sequencer state in minutes
            acquisition_timeout (int): timeout to retrieve acquisition state in minutes
        """
        super().__init__(config=config,
                         name=name,
                         host=host,
                         port=port,
                         cluster_name=cluster_name,
                         octave=octave,
                         close_other_machines=close_other_machines)

    def run(self, port: str):
        """Run the uploaded program"""

    def to_dict(self):
        """Return a dict representation of an OPX instrument."""
        return {RUNCARD.NAME: self.name.value} | self.settings.to_dict()
