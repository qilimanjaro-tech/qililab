"""
Class to interface with the local oscillator RohdeSchwarz SGS100A
"""
from dataclasses import dataclass

from qililab.connections import TCPIPConnection
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName, RohdeSchwarzSGS100A


@InstrumentFactory.register
class SGS100A(SignalGenerator, TCPIPConnection):
    """Rohde & Schwarz SGS100A class

    Args:
        device (RohdeSchwarz_SGS100A): Instance of the qcodes SGS100A class.
        settings (SGS100ASettings): Settings of the instrument.
    """

    name = InstrumentName.ROHDE_SCHWARZ

    @dataclass
    class SGS100ASettings(TCPIPConnection.TCPIPConnectionSettings, SignalGenerator.SignalGeneratorSettings):
        """Contains the settings of a specific pulsar."""

    settings: SGS100ASettings
    device: RohdeSchwarzSGS100A

    @TCPIPConnection.CheckConnected
    def setup(self):
        """Set R&S dbm power and frequency. Value ranges are:
        - power: (-120, 25).
        - frequency (1e6, 20e9).
        """
        self.device.power(self.power)
        self.device.frequency(self.frequency)

    @TCPIPConnection.CheckConnected
    def turn_on(self):
        """Start generating microwaves."""
        self.device.on()

    @TCPIPConnection.CheckConnected
    def stop(self):
        """Stop generating microwaves."""
        self.device.off()

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = RohdeSchwarzSGS100A(f"{self.name.value}_{self.id_}", f"TCPIP0::{self.address}::inst0::INSTR")

    def _device_name(self) -> str:
        """Gets the device Instrument name."""
        return self.name.value
