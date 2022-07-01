"""
Class to interface with the local oscillator RohdeSchwarz SGS100A
"""
from dataclasses import dataclass

from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName, RohdeSchwarzSGS100A


@InstrumentFactory.register
class SGS100A(SignalGenerator):
    """Rohde & Schwarz SGS100A class

    Args:
        device (RohdeSchwarz_SGS100A): Instance of the qcodes SGS100A class.
        settings (SGS100ASettings): Settings of the instrument.
    """

    name = InstrumentName.ROHDE_SCHWARZ

    @dataclass
    class SGS100ASettings(SignalGenerator.SignalGeneratorSettings):
        """Contains the settings of a specific pulsar."""

    settings: SGS100ASettings
    device: RohdeSchwarzSGS100A

    @SignalGenerator.CheckConnected
    def setup(self):
        """Set R&S dbm power and frequency. Value ranges are:
        - power: (-120, 25).
        - frequency (1e6, 20e9).
        """
        self.device.power(self.power)
        if self.frequency is not None:
            self.device.frequency(self.frequency)

    @SignalGenerator.frequency.setter  # type: ignore
    def frequency(self, value: float):
        """Set R&A frequency.

        Args:
            value (float): Frequency in Hz.
        """
        self.settings.frequency = value

    @SignalGenerator.CheckConnected
    def turn_on(self):
        """Start generating microwaves."""
        self.device.on()

    @SignalGenerator.CheckConnected
    def stop(self):
        """Stop generating microwaves."""
        self.device.off()

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = RohdeSchwarzSGS100A(f"{self.name.value}_{self.id_}", f"TCPIP0::{self.ip}::inst0::INSTR")
