"""Qblox Cluster Controller class"""
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.multi_instrument_controller import (
    MultiInstrumentController,
)
from qililab.instrument_controllers.utils.instrument_controller_factory import (
    InstrumentControllerFactory,
)
from qililab.instruments.qblox.qblox_qcm import QbloxQCM
from qililab.instruments.qblox.qblox_qrm import QbloxQRM
from qililab.typings.enums import (
    ConnectionName,
    InstrumentControllerName,
    InstrumentTypeName,
)
from qililab.typings.instruments.cluster import Cluster


@InstrumentControllerFactory.register
class QbloxClusterController(MultiInstrumentController):
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
    class QbloxClusterControllerSettings(MultiInstrumentController.MultiInstrumentControllerSettings):
        """Contains the settings of a specific Qblox Cluster Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: QbloxClusterControllerSettings

    def _initialize_device(self):
        """Initialize device controller."""
        self.device = Cluster(name=f"{self.name.value}_{self.id_}", identifier=self.address)

    def _set_device_to_all_modules(self):
        """Sets the initialized device to all attached modules,
        taking it from the Qblox Cluster device modules
        """
        for slot_id in self.connected_modules_slot_ids:
            self.modules[slot_id].device = self.device.modules[slot_id]

    @MultiInstrumentController.CheckConnected
    def reset(self):
        """Reset instrument."""
        super().reset()
        self.device.reset()

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, QbloxQCM) and not isinstance(module, QbloxQRM):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument are {InstrumentTypeName.QBLOX_QCM} "
                    + f"and {InstrumentTypeName.QBLOX_QRM}."
                )
