"""Attenuator class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName
from qililab.typings.enums import Parameter
from qililab.typings.instruments.mini_circuits import MiniCircuitsDriver


@InstrumentFactory.register
class Attenuator(Instrument):
    """Attenuator class.

    Args:
        name (InstrumentName): name of the instrument
        device (MiniCircuitsDriver): Instance of the MiniCircuitsDriver class.
        settings (StepAttenuatorSettings): Settings of the instrument.
    """

    name = InstrumentName.MINI_CIRCUITS

    @dataclass
    class StepAttenuatorSettings(Instrument.InstrumentSettings):
        """Step attenuator settings."""

        attenuation: float

    settings: StepAttenuatorSettings
    device: MiniCircuitsDriver

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set instrument settings."""
        if not isinstance(value, float):
            raise ValueError(f"Value must be a float. Current type is: {type(value)}")
        if parameter.value == Parameter.ATTENUATION.value:
            self.settings.attenuation = value
            self.device.setup(attenuation=self.attenuation)

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup."""
        self.device.setup(attenuation=self.attenuation)

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Turn off an instrument."""

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Turn on an instrument."""

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""

    @property
    def attenuation(self):
        """Attenuator 'attenuation' property.

        Returns:
            float: Attenuation.
        """
        return self.settings.attenuation
