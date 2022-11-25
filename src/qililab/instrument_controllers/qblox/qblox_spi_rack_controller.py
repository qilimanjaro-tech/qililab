"""Qblox SPI Rack Controller class"""
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.multi_instrument_controller import (
    MultiInstrumentController,
)
from qililab.instrument_controllers.utils.instrument_controller_factory import (
    InstrumentControllerFactory,
)
from qililab.instruments.qblox.qblox_d5a import QbloxD5a
from qililab.instruments.qblox.qblox_s4g import QbloxS4g
from qililab.typings.enums import (
    ConnectionName,
    InstrumentControllerName,
    InstrumentTypeName,
)
from qililab.typings.instruments.spi_rack import SPI_Rack


@InstrumentControllerFactory.register
class QbloxSPIRackController(MultiInstrumentController):
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
    class QbloxSPIRackControllerSettings(MultiInstrumentController.MultiInstrumentControllerSettings):
        """Contains the settings of a specific Qblox Cluster Controller."""

        reset = False

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.USB

    settings: QbloxSPIRackControllerSettings

    def _initialize_device(self):
        """Initialize device controller."""
        self.device = SPI_Rack(name=f"{self.name.value}_{self.id_}", address=self.address)

    def _set_device_to_all_modules(self):
        """Sets the initialized device to all attached modules,
        taking it from the Qblox Cluster device modules
        """
        # self.device.add_spi_module(3, "D5a")
        # self.device.add_spi_module(7, "S4g")
        # self.modules[0].device = self.device.module3
        # self.modules[1].device = self.device.module7
        for module, slot_id, reference in zip(self.modules, self.connected_modules_slot_ids, self.settings.modules):
            # FIXME: use the instrument name instead of the alias (it requires to save the name)
            self.device.add_spi_module(slot_id=slot_id - 1, module_type=reference.alias)
            module.device = self.device.modules[slot_id - 1]  # slot_id represents the number displayed in the cluster

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, QbloxD5a) and not isinstance(module, QbloxS4g):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument are {InstrumentTypeName.QBLOX_D5A} "
                    + f"and {InstrumentTypeName.QBLOX_S4G}."
                )
