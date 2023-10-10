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

"""Qblox SPI Rack Controller class"""
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.instrument_controller import InstrumentController, InstrumentControllerSettings
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.instruments.qblox.qblox_d5a import QbloxD5a
from qililab.instruments.qblox.qblox_s4g import QbloxS4g
from qililab.typings.enums import ConnectionName, InstrumentControllerName, InstrumentTypeName
from qililab.typings.instruments.spi_rack import SPI_Rack


@InstrumentControllerFactory.register
class QbloxSPIRackController(InstrumentController):
    """Qblox SPI Rack Controller class.

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        number_available_modules (int): Number of modules available in the
            Instrument Controller.
        settings (QbloxSPIRackControllerSettings): Settings of the Qblox SPI
            Rack Instrument Controller.
    """

    name = InstrumentControllerName.QBLOX_SPIRACK
    number_available_modules = 12
    device: SPI_Rack
    modules: Sequence[QbloxD5a | QbloxS4g]

    @dataclass
    class QbloxSPIRackControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific Qblox Cluster Controller."""

        reset = False

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.USB

    settings: QbloxSPIRackControllerSettings

    def _initialize_device(self):
        """Initialize device controller."""
        self.device = SPI_Rack(name=f"{self.name.value}_{self.alias}", address=self.address)

    def _set_device_to_all_modules(self):
        """Sets the initialized device to all attached modules,
        taking it from the Qblox Cluster device modules
        """
        for module, slot_id in zip(self.modules, self.connected_modules_slot_ids):
            self.device.add_spi_module(address=slot_id, module_type=module.name)
            module.device = self._module(module_id=slot_id)  # slot_id represents the number displayed in the cluster

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, QbloxD5a) and not isinstance(module, QbloxS4g):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument are {InstrumentTypeName.QBLOX_D5A} "
                    + f"and {InstrumentTypeName.QBLOX_S4G}."
                )

    def _module(self, module_id: int):
        """get module associated to the specific module id

        Args:
            module_id (int): slot index

        Returns:
            _type_: _description_
        """
        return getattr(self.device, f"module{module_id}")
