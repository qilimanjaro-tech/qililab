"""Qblox Pulsar Controller class"""
from dataclasses import dataclass

from qililab.instrument_controllers.qblox.qblox_controller import QbloxController
from qililab.instrument_controllers.single_instrument_controller import SingleInstrumentController
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.typings.enums import ConnectionName, InstrumentControllerName
from qililab.typings.instruments.pulsar import Pulsar


@InstrumentControllerFactory.register
class QbloxPulsarController(SingleInstrumentController, QbloxController):
    """Qblox Pulsar Controller class.

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        settings (QbloxPulsarControllerSettings): Settings of the Qblox Pulser Instrument Controller.
    """

    name = InstrumentControllerName.QBLOX_PULSAR
    device: Pulsar

    @dataclass
    class QbloxPulsarControllerSettings(
        SingleInstrumentController.SingleInstrumentControllerSettings, QbloxController.QbloxControllerSettings
    ):
        """Contains the settings of a specific Qblox Pulsar Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: QbloxPulsarControllerSettings

    def _initialize_device(self):
        """Initialize device controller."""
        self.device = Pulsar(name=f"{self.name.value}_{self.id_}", identifier=self.address)

    @QbloxController.CheckConnected
    def _set_reference_source(self):
        """Set reference source. Options are 'internal' or 'external'"""
        self.modules[0].device.reference_source(self.reference_clock.value)
