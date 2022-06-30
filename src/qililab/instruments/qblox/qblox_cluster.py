"""Qblox pulsar class"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from qililab.instruments.awg import AWG
from qililab.instruments.qblox.qblox_controller import QbloxController
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
    controller: Cluster
    n_modules: int = 20

    def __init__(self, settings: dict):
        super().__init__(settings=settings)

    def _initialize_controller(self):
        """Initialize device attribute to the corresponding device class."""
        # TODO: We need to update the firmware of the instruments to be able to connect
        # self.controller = Cluster(name=f"{self.name.value}_{self.id_}", identifier=self.ip)
        pass

    def create_modules(self):
        self.modules = [self.controller]
