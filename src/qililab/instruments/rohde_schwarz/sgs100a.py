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
        if parameter == Parameter.POWER:
            self.settings.power = float(value)
            self.device.power(self.power)
            return
        if parameter == Parameter.LO_FREQUENCY:
            self.settings.frequency = float(value)
            self.device.frequency(self.frequency)
            return
        if parameter == Parameter.RF_ON:
            value = bool(value)
            if value:
                self.turn_on()
            else:
                self.turn_off()
            return
        raise ValueError(f"Invalid Parameter: {parameter.value}")

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup"""
        self.device.power(self.power)
        self.device.frequency(self.frequency)
        if self.rf_on:
            self.device.on()
        else:
            self.device.off()

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Start generating microwaves."""
        self.settings.rf_on = True
        self.device.on()

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop generating microwaves."""
        self.settings.rf_on = False
        self.device.off()

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
