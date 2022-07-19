"""
Class to interface with the voltage source Qblox D5a
"""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.voltage_source import VoltageSource
from qililab.typings import InstrumentName
from qililab.typings import QbloxS4g as QbloxD5aDriver


@InstrumentFactory.register
class QbloxD5a(VoltageSource):
    """Qblox D5a class

    Args:
        name (InstrumentName): name of the instrument
        device (Qblox_D5a): Instance of the qcodes D5a class.
        settings (QbloxD5aSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_D5A

    @dataclass
    class QbloxD5aSettings(VoltageSource.VoltageSourceSettings):
        """Contains the settings of a specific signal generator."""

    settings: QbloxD5aSettings
    device: QbloxD5aDriver

    @Instrument.CheckDeviceInitialized
    def setup(self):
        """Set D5a voltage. Value ranges are:
        - voltage: (-8, 8)V.
        """
        self.device.dac0.voltage(self.voltage)
        # TODO: Implement more dacs

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup.
        For this instrument it is the same as a regular setup"""
        self.setup()

    @Instrument.CheckDeviceInitialized
    def start(self):
        """Dummy method."""

    @Instrument.CheckDeviceInitialized
    def stop(self):
        """Stop outputing voltage."""
        self.device.set_dacs_zero()

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        self.device.set_dacs_zero()
