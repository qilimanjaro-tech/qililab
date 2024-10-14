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

""" Quantum Machines Manager Instrument Controller """
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.instrument_controller import InstrumentControllerSettings
from qililab.instrument_controllers.single_instrument_controller import SingleInstrumentController
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.instruments.quantum_machines import QuantumMachinesCluster
from qililab.typings import QMMDriver
from qililab.typings.enums import InstrumentControllerName


@InstrumentControllerFactory.register
class QuantumMachinesClusterController(SingleInstrumentController):
    """Quantum Machines Manager class.

    This class implements the instrument controller for the Quantum Machines Manager instrument wrapper in Qililab.

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (QMMDriver): Instance of the Quantum Machines Manager Driver class.
        settings (QMMControllerSettings): Settings of the instrument.
    """

    name = InstrumentControllerName.QUANTUM_MACHINES_CLUSTER
    device: QMMDriver
    modules: Sequence[QuantumMachinesCluster]

    @dataclass
    class QuantumMachinesClusterControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific Quantum Machines Manager Controller."""

    settings: QuantumMachinesClusterControllerSettings

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = QMMDriver()

    def _check_supported_modules(self):
        """Checks if all instrument modules loaded are supported modules for the controller."""

    def _set_device_to_all_modules(self):
        """Sets the initialized device to all modules."""
        for module in self.modules:
            module.device = self.device
