"""Qblox controller class"""
from abc import abstractmethod
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
        """Contains the settings of a specific Qblox controller."""

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

    @TCPIPConnection.CheckConnected
    @abstractmethod
    def reset(self):
        """Reset instrument."""

    @TCPIPConnection.CheckConnected
    def initial_setup(self):
        """Initial setup of the instrument."""
        self.reset()
        self.create_modules()
        self.initialize_modules()

    @abstractmethod
    def create_modules(self):
        """Create the associated modules."""
        raise NotImplementedError()

    @abstractmethod
    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""

    @abstractmethod
    def _initialize_controller(self):
        """Initialize controller attribute to the corresponding Qblox device class."""

    def initialize_modules(self):
        """Initialize all modules with their setup."""
        for module in self.modules:
            module.initial_setup()

    @abstractmethod
    def _device_name(self) -> str:
        """Gets the device Instrument name."""
