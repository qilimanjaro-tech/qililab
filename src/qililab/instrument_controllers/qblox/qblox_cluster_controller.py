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
from typing import Sequence

from qililab.instrument_controllers.instrument_controller import InstrumentController, InstrumentControllerSettings
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.instruments.qblox.qblox_qcm import QbloxQCM
from qililab.instruments.qblox.qblox_qrm import QbloxQRM
from qililab.typings.enums import (
    ConnectionName,
    InstrumentControllerName,
    InstrumentTypeName,
    Parameter,
    ReferenceClock,
)
from qililab.typings.instruments.cluster import Cluster

EXT_TRIGGER_ADDRESS: int = 15


@InstrumentControllerFactory.register
class QbloxClusterController(InstrumentController):
    """Qblox Cluster Controller class.

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        number_available_modules (int): Number of modules available in the Instrument Controller.
        settings (QbloxClusterControllerSettings): Settings of the Qblox Pulser Instrument Controller.
    """

    name = InstrumentControllerName.QBLOX_CLUSTER
    number_available_modules = 20
    device: Cluster
    modules: Sequence[QbloxQCM | QbloxQRM]

    @dataclass
    class QbloxClusterControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific Qblox Cluster Controller."""

        reference_clock: ReferenceClock

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: QbloxClusterControllerSettings

    @InstrumentController.CheckConnected
    def initial_setup(self):
        """Initial setup of the Qblox Cluster Controller."""
        self._set_reference_source()
        if self.ext_trigger:
            self._set_ext_trigger()
        super().initial_setup()

    @InstrumentController.CheckConnected
    def reset(self):
        """Reset the device and clear cache of all modules."""
        self.device.reset()
        for module in self.modules:
            module.clear_cache()

    @InstrumentController.CheckConnected
    def _set_reference_source(self):
        """Set the reference source ('internal' or 'external')."""
        self.device.reference_source(self.reference_clock.value)

    @InstrumentController.CheckConnected
    def _set_ext_trigger(self):
        """set the external trigger parameters"""
        self.device.ext_trigger_input_trigger_en(True)
        # As only one ext trigger is available the last address is selected
        self.device.ext_trigger_input_trigger_address(EXT_TRIGGER_ADDRESS)
        self.device.ext_trigger_input_delay(0)

    @property
    def reference_clock(self):
        """Get the reference clock setting."""
        return self.settings.reference_clock

    def _check_supported_modules(self):
        """Check if all loaded instrument modules are supported."""
        for module in self.modules:
            if not isinstance(module, (QbloxQCM, QbloxQRM)):
                raise ValueError(
                    f"Instrument {type(module)} not supported. "
                    f"The only supported instruments are {InstrumentTypeName.QBLOX_QCM} and {InstrumentTypeName.QBLOX_QRM}."
                )

    def _initialize_device(self):
        """Initialize the cluster device."""
        self.device = Cluster(name=f"{self.name.value}_{self.alias}", identifier=self.address)

    def _set_device_to_all_modules(self):
        """Set the initialized device to all attached modules."""
        for module, slot_id in zip(self.modules, self.connected_modules_slot_ids):
            module.device = self.device.modules[slot_id - 1]  # slot_id represents the number displayed in the cluster

    def to_dict(self):
        """Return a dictionary representation of the Qblox controller class."""
        return super().to_dict() | {
            Parameter.REFERENCE_CLOCK.value: self.reference_clock.value,
        }
