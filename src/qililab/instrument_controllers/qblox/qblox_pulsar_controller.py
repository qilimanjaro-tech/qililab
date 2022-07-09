"""Qblox Pulsar Controller class"""
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.single_instrument_controller import (
    SingleInstrumentController,
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
from qililab.typings.instruments.pulsar import Pulsar


@InstrumentControllerFactory.register
class QbloxPulsarController(SingleInstrumentController):
    """Qblox Pulsar Controller class.

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        settings (QbloxPulsarControllerSettings): Settings of the Qblox Pulser Instrument Controller.
    """

    name = InstrumentControllerName.QBLOX_PULSAR
    device: Pulsar
    modules: Sequence[QbloxQCM | QbloxQRM]

    @dataclass
    class QbloxPulsarControllerSettings(SingleInstrumentController.SingleInstrumentControllerSettings):
        """Contains the settings of a specific Qblox Pulsar Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: QbloxPulsarControllerSettings

    def _initialize_device(self):
        """Initialize device controller."""
        self.device = Pulsar(name=f"{self.name.value}_{self.id_}", identifier=self.address)

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, QbloxQCM) and not isinstance(module, QbloxQRM):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument are {InstrumentTypeName.QBLOX_QCM} "
                    + f"and {InstrumentTypeName.QBLOX_QRM}."
                )
