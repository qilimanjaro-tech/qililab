""" Agilent E5071B Instrument Controller """
from dataclasses import dataclass
from typing import Sequence

from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.instrument_controllers.vector_network_analyzer.vector_network_analyzer_controller import (
    VectorNetworkAnalyzerController,
)
from qililab.instruments.agilent.e5071b_vna import E5071B
from qililab.typings.enums import InstrumentControllerName, InstrumentName
from qililab.typings.instruments.agilent_e5071b import E5071BDriver


@InstrumentControllerFactory.register
class E5071BController(VectorNetworkAnalyzerController):
    """Agilent E5071B Instrument Controller

    Args:
        name (InstrumentControllerName): Name of the Instrument Controller.
        device (RohdeSchwarz_E5071B): Instance of the qcodes E5071B class.
        settings (E5071BSettings): Settings of the instrument.
    """

    name = InstrumentControllerName.AGILENT_E5071B
    device: E5071BDriver
    modules: Sequence[E5071B]

    @dataclass
    class E5071BControllerSettings(VectorNetworkAnalyzerController.VectorNetworkAnalyzerControllerSettings):
        """Contains the settings of a specific E5071B Controller."""

    settings: E5071BControllerSettings

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = E5071BDriver(name=f"{self.name.value}_{self.id_}", address=self.address, timeout=self.timeout)

    def _check_supported_modules(self):
        """check if all instrument modules loaded are supported modules for the controller."""
        for module in self.modules:
            if not isinstance(module, E5071B):
                raise ValueError(
                    f"Instrument {type(module)} not supported."
                    + f"The only supported instrument is {InstrumentName.AGILENT_E5071B}"
                )
