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

""" Quantum Machines OPX Instrument Controller """
from dataclasses import dataclass

from qililab.instrument_controllers.instrument_controller import InstrumentControllerSettings
from qililab.instrument_controllers.single_instrument_controller import SingleInstrumentController
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.typings import QMMDriver
from qililab.typings.enums import InstrumentControllerName


@InstrumentControllerFactory.register
class QMMController(SingleInstrumentController):
    """Quantum Machines Manager class.

    This class implements the instrument controller for the Quantum Machines Manager instrument wrapper in Qililab.

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (QMMDriver): Instance of the Quantum Machines Manager Driver class.
        settings (QMMControllerSettings): Settings of the instrument.
    """

    name = InstrumentControllerName.QMM
    device: QMMDriver

    @dataclass
    class QMMControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific Quantum Machines Manager Controller."""

    settings: QMMControllerSettings

    def _initialize_device(self):
        """Initialize device controller."""
        self.device = QMMDriver(name=f"{self.name.value}_{self.alias}", identifier=self.address)
