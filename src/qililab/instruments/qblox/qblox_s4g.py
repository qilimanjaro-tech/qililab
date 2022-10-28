"""
Class to interface with the voltage source Qblox S4g
"""
from dataclasses import dataclass
from time import sleep

from qililab.instruments.current_source import CurrentSource
from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName
from qililab.typings import QbloxS4g as QbloxS4gDriver


@InstrumentFactory.register
class QbloxS4g(CurrentSource):
    """Qblox S4g class

    Args:
        name (InstrumentName): name of the instrument
        device (Qblox_S4g): Instance of the qcodes S4g class.
        settings (QbloxS4gSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_S4G

    @dataclass
    class QbloxS4gSettings(CurrentSource.CurrentSourceSettings):
        """Contains the settings of a specific signal generator."""

    settings: QbloxS4gSettings
    device: QbloxS4gDriver

    @Instrument.CheckDeviceInitialized
    def setup(self):
        """Set S4g current. Value ranges are:
        - current: (-40, 40)mA.
        """
        self.device.dac0.ramping_enabled(self.ramping_enabled)
        self.device.dac0.ramp_rate(self.ramp_rate)
        self.device.dac0.span(self.span)
        self.device.dac0.current(self.current)
        print(f'SPI current set to {self.device.dac0.current()}')
        while self.device.dac0.is_ramping():
            sleep(0.1)
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
        """Stop outputing current."""
        self.device.dac0.current(0.0)
        sleep(0.1)
        print(f'Current resetted to {self.device.dac0.current()}')

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        # self.device.set_dacs_zero()
