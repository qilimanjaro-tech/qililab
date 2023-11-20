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

"""Qblox Pulsar Controller class"""
from dataclasses import dataclass

from qililab.instrument_controllers.qblox.qblox_controller import QbloxController
from qililab.instrument_controllers.single_instrument_controller import SingleInstrumentController
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.typings.enums import ConnectionName, InstrumentControllerName
from qililab.typings.instruments.pulsar import Pulsar


@InstrumentControllerFactory.register
class QbloxPulsarController(SingleInstrumentController, QbloxController):
    """Qblox Pulsar Controller class.

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        settings (QbloxPulsarControllerSettings): Settings of the Qblox Pulser Instrument Controller.
    """

    name = InstrumentControllerName.QBLOX_PULSAR
    device: Pulsar

    @dataclass
    class QbloxPulsarControllerSettings(QbloxController.QbloxControllerSettings):
        """Contains the settings of a specific Qblox Pulsar Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: QbloxPulsarControllerSettings

    def _initialize_device(self):
        """Initialize device controller."""
        self.device = Pulsar(name=f"{self.name.value}_{self.alias}", identifier=self.address)

    @QbloxController.CheckConnected
    def _set_reference_source(self):
        """Set reference source. Options are 'internal' or 'external'"""
        self.modules[0].device.reference_source(self.reference_clock.value)
