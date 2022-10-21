""" KeySight E5080B Instrument Controller """
from dataclasses import dataclass
from typing import Sequence

from qililab.constants import DEFAULT_TIMEOUT
from qililab.instrument_controllers.single_instrument_controller import (
    SingleInstrumentController,
)
from qililab.instrument_controllers.utils.instrument_controller_factory import (
    InstrumentControllerFactory,
)
from qililab.instruments.keysight.e5080b_vna import E5080B
from qililab.typings import E5080BDriver
from qililab.typings.enums import (
    ConnectionName,
    InstrumentControllerName,
    InstrumentName,
)


@InstrumentControllerFactory.register
class E5080BController(SingleInstrumentController):
    """KeySight E5080B Instrument Controller

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (RohdeSchwarz_E5080B): Instance of the qcodes E5080B class.
        settings (E5080BSettings): Settings of the instrument.
    """

    name = InstrumentControllerName.KEYSIGHT_E5080B
    device: E5080BDriver
    modules: Sequence[E5080B]

    @dataclass
    class E5080BControllerSettings(SingleInstrumentController.SingleInstrumentControllerSettings):
        """Contains the settings of a specific E5080B Controller."""

        timeout: float = DEFAULT_TIMEOUT

        def __post_init__(self):
            super().__post_init__()
            self.connection.name = ConnectionName.TCP_IP

    settings: E5080BControllerSettings

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = E5080BDriver(name=f"{self.name.value}_{self.id_}", address=self.address, timeout=self.timeout)

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, E5080B):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument is {InstrumentName.KEYSIGHT_E5080B}"
                )

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
