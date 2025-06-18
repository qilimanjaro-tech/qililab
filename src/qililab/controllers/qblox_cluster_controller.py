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
from __future__ import annotations

from qililab.controllers.controller import Controller
from qililab.controllers.controller_factory import ControllerFactory
from qililab.controllers.controller_type import ControllerType
from qililab.controllers.devices import QbloxClusterDevice
from qililab.runcard.runcard_controllers import (
    QbloxClusterRuncardController,
    RuncardController,
)
from qililab.settings.controllers import QbloxClusterControllerSettings


@ControllerFactory.register(ControllerType.QBLOX_CLUSTER_CONTROLLER)
class QbloxClusterController(Controller[QbloxClusterDevice, QbloxClusterControllerSettings]):
    MAX_RAMPING_RATE: float = 2e7

    @classmethod
    def get_default_settings(cls) -> QbloxClusterControllerSettings:
        return QbloxClusterControllerSettings(alias="qblox_cluster", modules={})

    def _initialize_device(self):
        self.device = QbloxClusterDevice(name=f"{self.settings.alias}", identifier=self.settings.connection.address)

    def to_runcard(self) -> RuncardController:
        return QbloxClusterRuncardController(settings=self.settings)

    def _get_voltage(self, channel: int):
        return self.device.channel(channel).dc_constant_V()

    def _set_voltage(self, value: float, channel: int):
        self.device.channel(channel).dc_constant_V(value)

    def _get_span(self, channel: int):
        return self.device.channel(channel).output_range()

    def _set_span(self, value: str, channel: int):
        self.device.channel(channel).output_range(value)

    def _get_ramping_rate(self, channel: int):
        return self.device.channel(channel).dc_slew_rate_V_per_s()

    def _set_ramping_rate(self, value: float, channel: int):
        self.device.channel(channel).dc_slew_rate_V_per_s(value)

    def _get_low_pass_filter(self, channel: int):
        return self.device.channel(channel).output_filter()

    def _set_low_pas_filter(self, value: str, channel: int):
        self.device.channel(channel).output_filter(value)
