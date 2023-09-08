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

""" Agilent E5071B Instrument Controller """
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.instrument_controllers.vector_network_analyzer.vector_network_analyzer_controller import (
    VectorNetworkAnalyzerController,
)
from qililab.instruments.agilent.e5071b_vna import E5071B
from qililab.typings.enums import InstrumentControllerName, InstrumentName
from qililab.typings.instruments.vector_network_analyzer import VectorNetworkAnalyzerDriver


@InstrumentControllerFactory.register
class E5071BController(VectorNetworkAnalyzerController):
    """Agilent E5071B Instrument Controller

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (RohdeSchwarz_E5071B): Instance of the qcodes E5071B class.
        settings (E5071BSettings): Settings of the instrument.
    """

    name = InstrumentControllerName.AGILENT_E5071B
    device: VectorNetworkAnalyzerDriver
    modules: Sequence[E5071B]

    @dataclass
    class E5071BControllerSettings(VectorNetworkAnalyzerController.VectorNetworkAnalyzerControllerSettings):
        """Contains the settings of a specific E5071B Controller."""

    settings: E5071BControllerSettings

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = VectorNetworkAnalyzerDriver(
            name=f"{self.name.value}_{self.alias}", address=self.address, timeout=self.timeout
        )

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, E5071B):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument is {InstrumentName.AGILENT_E5071B}"
                )
