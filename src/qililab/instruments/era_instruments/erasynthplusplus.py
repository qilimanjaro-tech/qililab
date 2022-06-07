"""
Class to interface with the local oscillator EraSynth++
"""
from qililab.instruments.signal_generator import SignalGenerator
from qililab.typings import BusElementName, EraSynthPlusPlus as QCoDeSEraSynthPlusPlus
from qililab.utils import Factory, nested_dataclass


@Factory.register
class EraSynthPlusPlus(SignalGenerator):
    """EraSynthPlusPlus class

    Args:
        device (EraSynthPlusPlus): Instance of the qcodes EraSynthPlusPlus class.
        settings (EraSynthSettings): Settings of the instrument.
    """

    name = BusElementName.ERASYNTH

    @nested_dataclass
    class EraSynthSettings(SignalGenerator.SignalGeneratorSettings):
        """Contains the settings of a specific pulsar."""

    device: QCoDeSEraSynthPlusPlus
    settings: EraSynthSettings

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = self.EraSynthSettings(**settings)

    @SignalGenerator.CheckConnected
    def setup(self):
        """Set EraSynth dbm power and frequency. Value ranges are:
        # TODO: Add actual values for the EraSynth++, these are from the R&S
        - power: (-120, 25).
        - frequency (1e6, 20e9).
        """
        self.device.power(self.power)
        self.device.frequency(self.frequency)

    @SignalGenerator.CheckConnected
    def start(self):
        """Start generating microwaves."""
        self.device.on()

    @SignalGenerator.CheckConnected
    def stop(self):
        """Stop generating microwaves."""
        self.device.off()

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = QCoDeSEraSynthPlusPlus(f"{self.name}_{self.id_}", self.ip)
