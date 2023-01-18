"""
Class to interface with the local oscillator RohdeSchwarz SGS100A
"""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import EraSynthPlusPlus as QCoDeSEraSynthPlusPlus
from qililab.typings import InstrumentName
from qililab.typings.enums import Parameter


@InstrumentFactory.register
class EraSynthPlusPlus(SignalGenerator):
    """EraSynthPlusPlus class

    Args:
        name (InstrumentName): name of the instrument
        device (EraSynthPlusPlus): Instance of the qcodes EraSynthPlusPlus class.
        settings (EraSynthSettings): Settings of the instrument.
    """

    name = InstrumentName.ERASYNTH

    @dataclass
    class EraSynthPlusPlusSettings(SignalGenerator.SignalGeneratorSettings):
        """Contains the settings of a specific signal generator."""

    settings: EraSynthPlusPlusSettings
    device: QCoDeSEraSynthPlusPlus

    @Instrument.CheckDeviceInitialized
    @Instrument.CheckParameterValueFloatOrInt
    def setup(
        self,
        parameter: Parameter,
        value: float | str | bool,
        channel_id: int | None = None,
    ):
        """Set EraSynthPlusPlus dbm power and frequency. Value ranges are:
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
        raise ValueError(f"Invalid Parameter: {parameter.value}")

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup"""
        self.device.power(self.power)
        self.device.frequency(self.frequency)

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
