"""
Class to interface with the local oscillator RohdeSchwarz SGS100A
"""
from qililab.instruments.signal_generator import SignalGenerator
from qililab.settings import SGS100ASettings
from qililab.typings import RohdeSchwarzSGS100A


class SGS100A(SignalGenerator):
    """Rohde & Schwarz SGS100A class

    Args:
        name (str): Name of the instrument.
        device (RohdeSchwarz_SGS100A): Instance of the qcodes SGS100A class.
        settings (SGS100ASettings): Settings of the instrument.
    """

    device: RohdeSchwarzSGS100A
    settings: SGS100ASettings

    def __init__(self, name: str, settings: dict):
        super().__init__(name=name)
        self.settings = SGS100ASettings(**settings)

    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""
        if not self._connected:
            self.device = RohdeSchwarzSGS100A(self.name, f"TCPIP0::{self.settings.ip}::inst0::INSTR")
            self._connected = True

    def setup(self):
        """Set R&S dbm power and frequency. Value ranges are:
        - power: (-120, 25).
        - frequency (1e6, 20e9).
        """
        self.device.power(self.settings.power)
        self.device.frequency(self.settings.frequency)

    def start(self):
        """Start generating microwaves."""
        self.device.on()

    def stop(self):
        """Stop generating microwaves."""
        self.device.off()
