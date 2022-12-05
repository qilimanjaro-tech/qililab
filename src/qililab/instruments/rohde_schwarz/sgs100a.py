"""
Class to interface with the local oscillator RohdeSchwarz SGS100A
"""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName, RohdeSchwarzSGS100A
from qililab.typings.enums import Parameter


@InstrumentFactory.register
class SGS100A(SignalGenerator):
    """Rohde & Schwarz SGS100A class

    Args:
        name (InstrumentName): name of the instrument
        device (RohdeSchwarz_SGS100A): Instance of the qcodes SGS100A class.
        settings (SGS100ASettings): Settings of the instrument.
    """

    name = InstrumentName.ROHDE_SCHWARZ

    @dataclass
    class SGS100ASettings(SignalGenerator.SignalGeneratorSettings):
        """Contains the settings of a specific signal generator."""

    settings: SGS100ASettings
    device: RohdeSchwarzSGS100A

    @Instrument.CheckDeviceInitialized
    def setup(
        self,
        parameter: Parameter,
        value: float | str | bool,
        channel_id: int | None = None,
    ):
        """Set R&S dbm power and frequency. Value ranges are:
        - power: (-120, 25).
        - frequency (1e6, 20e9).
        """
        if not isinstance(value, float):
            raise ValueError(f"Value must be a float. Current type is: {type(value)}")
        if parameter == Parameter.POWER:
            self.settings.power = value
            self.device.power(self.power)
        if parameter == Parameter.FREQUENCY:
            self.settings.frequency = value
            self.device.frequency(self.frequency)

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup"""
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

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Start generating microwaves."""
        self.device.on()

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop generating microwaves."""
        self.device.off()

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
