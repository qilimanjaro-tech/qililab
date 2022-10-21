""" Vector Network Analyzer General Instrument Controller """
from dataclasses import dataclass

from qililab.constants import DEFAULT_TIMEOUT
from qililab.instrument_controllers.single_instrument_controller import (
    SingleInstrumentController,
)
from qililab.typings.enums import ConnectionName
from qililab.typings.instruments.vector_network_analyzer import (
    VectorNetworkAnalyzerDriver,
)


class VectorNetworkAnalyzerController(SingleInstrumentController):
    """Vector Network Analyzer General Instrument Controller

    Args:
        settings (VectorNetworkAnalyzerControllerSettings): Settings of the instrument controller.
    """

    @dataclass
    class VectorNetworkAnalyzerControllerSettings(SingleInstrumentController.SingleInstrumentControllerSettings):
        """Contains the settings of a specific VectorNetworkAnalyzer Controller."""

        timeout: float = DEFAULT_TIMEOUT

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: VectorNetworkAnalyzerControllerSettings
    device: VectorNetworkAnalyzerDriver

    @property
    def timeout(self):
        """VectorNetworkAnalyzer 'timeout' property.

        Returns:
            float: settings.timeout.
        """
        return self.settings.timeout

    @timeout.setter
    def timeout(self, value: float):
        """sets the timeout"""
        self.settings.timeout = value
        self.device.set_timeout(value=self.settings.timeout)
