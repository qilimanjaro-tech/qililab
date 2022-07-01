"""Qblox pulsar class"""
from abc import abstractmethod
from dataclasses import dataclass
from typing import List

from qililab.instruments.qblox.qblox_controller import QbloxController
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.typings import Cluster


class QbloxCluster(QbloxController):
    """Qblox pulsar class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    @dataclass
    class QbloxClusterSettings(QbloxController.QbloxControllerSettings):
        """Contains the settings of a specific pulsar."""

    settings: QbloxClusterSettings
    device: Cluster
    n_modules: int = 20
    modules_connected: List[int]

    def __init__(self, settings: dict):
        super().__init__(settings=settings)

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = Cluster(name=f"{self._device_name()}_{self._device_identifier()}", identifier=self.address)

    def create_modules(self):
        """Create the associated modules."""
        for slot_id in self.modules_connected:
            cluster_module = QbloxModule(self.device.modules[slot_id], slot_id=slot_id, settings=self.settings)
            self.modules.append(cluster_module)

    @abstractmethod
    def _device_name(self) -> str:
        """Gets the device Instrument name."""

    @abstractmethod
    def _device_identifier(self) -> str:
        """Gets the device identifier."""
