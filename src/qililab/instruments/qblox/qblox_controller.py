"""Qblox controller class"""
from abc import abstractclassmethod
from dataclasses import dataclass
from typing import List

from qililab.connections.tcpip_connection import TCPIPConnection
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.typings import Cluster, Pulsar


class QbloxController(TCPIPConnection):
    """Qblox controller class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    @dataclass
    class QbloxControllerSettings(TCPIPConnection.TCPIPConnectionSettings):
        """Contains the settings of a specific Qblox controller.

        Args:
            reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
            sequencer (int): Index of the sequencer to use.
            sync_enabled (bool): Enable synchronization over multiple instruments.
            gain (float): Gain step used by the sequencer.
        """

    settings: QbloxControllerSettings
    modules: List[QbloxModule]
    n_modules: int
    controller: Pulsar | Cluster

    def __init__(self, settings: dict):
        super().__init__(settings=settings)

    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""
        super().connect()
        self.initial_setup()

    def reset(self):
        """Reset instrument."""
        self.controller.reset()

    def initial_setup(self):
        """Initial setup of the instrument."""
        self.reset()
        self.create_modules()
        self.initialize_modules()

    @abstractclassmethod
    def create_modules(self):
        raise NotImplementedError()

    def _initialize_controller(self):
        """Initialize device attribute to the corresponding device class."""
        self._initialize_controller()

    def initialize_modules(self):
        for module in self.modules:
            module.initial_setup()
