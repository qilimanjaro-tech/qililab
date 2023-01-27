""" EraSynthPlusPlus Instrument Controller """
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.single_instrument_controller import (
    SingleInstrumentController,
)
from qililab.instrument_controllers.utils.instrument_controller_factory import (
    InstrumentControllerFactory,
)
from qililab.instruments.era.erasynthplusplus import EraSynthPlusPlus
from qililab.typings import EraSynthPlusPlus as QCoDeSEraSynthPlusPlus
from qililab.typings.enums import (
    ConnectionName,
    InstrumentControllerName,
    InstrumentTypeName,
)


@InstrumentControllerFactory.register
class EraSynthPlusPlusController(SingleInstrumentController):
    """EraSynthPlusPlus class

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (EraSynthPlusPlus): Instance of the qcodes EraSynthPlusPlus class.
        settings (EraSynthPlusPlusSettings): Settings of the instrument.
    """

    name = InstrumentControllerName.ERASYNTH
    device: QCoDeSEraSynthPlusPlus
    modules: Sequence[EraSynthPlusPlus]

    @dataclass
    class EraSynthPlusPlusControllerSettings(SingleInstrumentController.SingleInstrumentControllerSettings):
        """Contains the settings of a specific EraSynthPlusPlus Controller."""

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.USB.value

    settings: EraSynthPlusPlusControllerSettings

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = QCoDeSEraSynthPlusPlus(f"{self.name.value}_{self.id_}", f"TCPIP0::{self.address}::inst0::INSTR")

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, EraSynthPlusPlus):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument is {InstrumentTypeName.ERA}"
                )
