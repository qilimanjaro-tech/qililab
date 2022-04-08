"""
Class to interface with the local oscillator RohdeSchwarz SGS100A
"""
from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarz_SGS100A

from qililab.instruments.signal_generator import SignalGenerator
from qililab.settings import SETTINGS_MANAGER
from qililab.settings.instruments.rohde_schwarz.sgs100a import SGS100ASettings


class SGS100A(SignalGenerator):
    """Rohde & Schwarz SGS100A class

    Args:
        name (str): Name of the instrument.
        device (RohdeSchwarz_SGS100A): Instance of the qcodes SGS100A class.
        settings (SGS100ASettings): Settings of the instrument.
    """

    def __init__(self, name: str):
        super().__init__(name=name)
        self.device: RohdeSchwarz_SGS100A | None = None
        self.settings = self.load_settings()

    def load_settings(self):
        """Load instrument settings"""
        settings = SETTINGS_MANAGER.load(filename=self.name)
        if not isinstance(settings, SGS100ASettings):
            raise ValueError(f"""Using instance of class {type(settings).__name__} instead of class SGS100ASettings.""")
        return settings

    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""
        if not self._connected:
            self.device = RohdeSchwarz_SGS100A(self.name, f"TCPIP0::{self.settings.ip}::inst0::INSTR")
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

    def close(self):
        """Close connection with the instrument."""
        if self._connected:
            self.stop()
            self.device.close()
            self._connected = False
