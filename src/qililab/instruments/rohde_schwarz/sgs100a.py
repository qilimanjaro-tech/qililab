"""
Class to interface with the local oscillator RohdeSchwarz SGS100A
"""
from qililab.instruments.signal_generator import SignalGenerator
from qililab.typings import BusElementName, RohdeSchwarzSGS100A
from qililab.utils import Factory, nested_dataclass


@Factory.register
class SGS100A(SignalGenerator):
    """Rohde & Schwarz SGS100A class

    Args:
        device (RohdeSchwarz_SGS100A): Instance of the qcodes SGS100A class.
        settings (SGS100ASettings): Settings of the instrument.
    """

    name = BusElementName.ROHDE_SCHWARZ

    @nested_dataclass
    class SGS100ASettings(SignalGenerator.SignalGeneratorSettings):
        """Contains the settings of a specific pulsar."""

    device: RohdeSchwarzSGS100A
    settings: SGS100ASettings

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = self.SGS100ASettings(**settings)

    @SignalGenerator.CheckConnected
    def setup(self):
        """Set R&S dbm power and frequency. Value ranges are:
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
        self.device = RohdeSchwarzSGS100A(f"{self.name.value}_{self.id_}", f"TCPIP0::{self.ip}::inst0::INSTR")
