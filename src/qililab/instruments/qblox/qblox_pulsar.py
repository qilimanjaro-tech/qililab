"""Qblox pulsar class"""
from abc import abstractmethod
from dataclasses import dataclass

from qililab.instruments.qblox.qblox_controller import QbloxController
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.typings import Pulsar


class QbloxPulsar(QbloxController):
    """Qblox pulsar class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    @dataclass
    class QbloxPulsarSettings(QbloxController.QbloxControllerSettings):
        """Contains the settings of a specific pulsar."""

    settings: QbloxPulsarSettings
    device: Pulsar
    n_modules: int = 1

    def __init__(self, settings: dict):
        super().__init__(settings=settings)

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = Pulsar(name=f"{self._device_name()}_{self._device_identifier()}", identifier=self.address)

    def create_modules(self):
        """Create the associated modules."""
        pulsar_module = QbloxModule(self.device, slot_id=0, settings=self.settings)
        self.modules = [pulsar_module]

    @abstractmethod
    def _device_name(self) -> str:
        """Gets the device Instrument name."""

    @abstractmethod
    def _device_identifier(self) -> str:
        """Gets the device identifier."""
