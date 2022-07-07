"""Qblox Cluster Controller class"""
from dataclasses import dataclass

from qililab.connections.connection import Connection
from qililab.instrument_controllers.multi_instrument_controller import (
    MultiInstrumentController,
)
from qililab.instrument_controllers.utils.instrument_controller_factory import (
    InstrumentControllerFactory,
)
from qililab.typings.enums import ConnectionName, InstrumentControllerName
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

    @dataclass
    class QbloxClusterControllerSettings(MultiInstrumentController.MultiInstrumentControllerSettings):
        """Contains the settings of a specific Qblox Cluster Controller."""

        def __post_init__(self):
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

    @Connection.CheckConnected
    def reset(self):
        """Reset instrument."""
        super().reset()
        self.device.reset()
