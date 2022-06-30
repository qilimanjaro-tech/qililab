"""Qblox pulsar class"""
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
    controller: Pulsar
    n_modules: int = 1

    def __init__(self, settings: dict):
        super().__init__(settings=settings)

    def _initialize_controller(self):
        """Initialize device attribute to the corresponding device class."""
        # TODO: We need to update the firmware of the instruments to be able to connect
        # self.controller = Pulsar(name=f"{self.name.value}_{self.id_}", identifier=self.ip)
        pass

    def create_modules(self):
        pulsar_module = QbloxModule(self.controller, slot_id=0, settings=self.settings)
        self.modules = [pulsar_module]
