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

"""Qblox Cluster Controller class"""
from dataclasses import dataclass

from qililab.instrument_controllers.qblox.qblox_controller import QbloxController
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.typings.enums import ConnectionName, InstrumentControllerName
from qililab.typings.instruments.cluster import Cluster


@InstrumentControllerFactory.register
class QbloxClusterController(QbloxController):
    """Qblox Cluster Controller class.

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        number_available_modules (int): Number of modules available in the Instrument Controller.
        settings (QbloxClusterControllerSettings): Settings of the Qblox Pulser Instrument Controller.
    """

    name = InstrumentControllerName.QBLOX_CLUSTER
    number_available_modules = 20
    device: Cluster

    @dataclass
    class QbloxClusterControllerSettings(QbloxController.QbloxControllerSettings):
        """Contains the settings of a specific Qblox Cluster Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: QbloxClusterControllerSettings

    def _initialize_device(self):
        """Initialize device controller."""
        self.device = Cluster(name=f"{self.name.value}_{self.alias}", identifier=self.address)

    def _set_device_to_all_modules(self):
        """Sets the initialized device to all attached modules,
        taking it from the Qblox Cluster device modules
        """
        for module, slot_id in zip(self.modules, self.connected_modules_slot_ids):
            module.device = self.device.modules[slot_id - 1]  # slot_id represents the number displayed in the cluster

    @QbloxController.CheckConnected
    def reset(self):
        """Reset instrument."""
        self.device.reset()
        for module in self.modules:
            module.clear_cache()

    @QbloxController.CheckConnected
    def _set_reference_source(self):
        """Set reference source. Options are 'internal' or 'external'"""
        self.device.reference_source(self.reference_clock.value)
