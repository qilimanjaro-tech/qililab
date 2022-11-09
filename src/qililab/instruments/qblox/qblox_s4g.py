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

    def dac(self, dac_index: int):
        """get channel associated to the specific dac

        Args:
            dac_index (int): channel index

        Returns:
            _type_: _description_
        """
        return getattr(self.device, f"dac{dac_index}")

    def _channel_setup(self, dac_index: int) -> None:
        """Setup for a specific dac channel

        Args:
            dac_index (int): dac specific index channel
        """
        channel = self.dac(dac_index=dac_index)
        channel.ramping_enabled(self.ramping_enabled[dac_index])
        channel.ramp_rate(self.ramp_rate[dac_index])
        channel.span(self.span[dac_index])
        channel.current(self.current[dac_index])
        print(f"SPI current set to {channel.current()}")
        while channel.is_ramping():
            sleep(0.1)

    @Instrument.CheckDeviceInitialized
    def setup(self):
        """Set S4g current. Value ranges are:
        - current: (-40, 40)mA.
        """
        for channel_index in self.dacs:
            self._channel_setup(dac_index=channel_index)

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
        # self.device.dac0.current(0.0)
        # sleep(0.1)
        # print(f'Current resetted to {self.device.dac0.current()}')

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        # self.device.set_dacs_zero()
