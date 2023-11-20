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

""" Vector Network Analyzer General Instrument Controller """
from dataclasses import dataclass

from qililab.constants import DEFAULT_TIMEOUT
from qililab.instrument_controllers.instrument_controller import InstrumentControllerSettings
from qililab.instrument_controllers.single_instrument_controller import SingleInstrumentController
from qililab.typings.enums import ConnectionName
from qililab.typings.instruments.vector_network_analyzer import VectorNetworkAnalyzerDriver


class VectorNetworkAnalyzerController(SingleInstrumentController):
    """Vector Network Analyzer General Instrument Controller

    Args:
        settings (VectorNetworkAnalyzerControllerSettings): Settings of the instrument controller.
    """

    @dataclass
    class VectorNetworkAnalyzerControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific VectorNetworkAnalyzer Controller."""

        timeout: float = DEFAULT_TIMEOUT

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: VectorNetworkAnalyzerControllerSettings
    device: VectorNetworkAnalyzerDriver

    @property
    def timeout(self):
        """VectorNetworkAnalyzer 'timeout' property.

        Returns:
            float: settings.timeout.
        """
        return self.settings.timeout

    @timeout.setter
    def timeout(self, value: float):
        """sets the timeout"""
        self.settings.timeout = value
        self.device.set_timeout(value=self.settings.timeout)
