"""Attenuator class."""
from dataclasses import dataclass

from qililab.connections import TCPIPConnection
from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName
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

    @TCPIPConnection.CheckConnected
    def setup(self):
        """Set instrument settings."""
        self.device.setup(attenuation=self.attenuation)

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup.
        For this instrument it is the same as a regular setup"""
        self.setup()

    @Instrument.CheckDeviceInitialized
    def start(self):
        """Start generating microwaves."""

    @Instrument.CheckDeviceInitialized
    def stop(self):
        """Stop generating microwaves."""

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
