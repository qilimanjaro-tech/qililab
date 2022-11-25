"""
Class to interface with the voltage source Qblox D5a
"""

from dataclasses import dataclass
from time import sleep

from qililab.config import logger
from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.voltage_source import VoltageSource
from qililab.typings import InstrumentName
from qililab.typings import QbloxD5a as QbloxD5aDriver
from qililab.typings.enums import Parameter


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
        channel.voltage(self.voltage[dac_index])
        logger.debug("SPI voltage set to %f", channel.voltage())
        while channel.is_ramping():
            sleep(0.1)

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set Qblox instrument calibration settings."""

        if channel_id is None:
            raise ValueError("channel not specified to update instrument")
        if channel_id > 3:
            raise ValueError(
                f"the specified dac index:{channel_id} is out of range."
                + " Number of dacs is 4 -> maximum channel_id should be 3."
            )
        if parameter.value == Parameter.VOLTAGE.value:
            if not isinstance(value, float):
                raise ValueError(f"value type must be a float. Current type is {type(value)}")
            self.settings.voltage[channel_id] = value
            channel = self.dac(dac_index=channel_id)
            channel.voltage(self.voltage[channel_id])
            return
        raise ValueError(f"Invalid Parameter: {parameter.value}")

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup."""
        for dac_index, voltage_value in enumerate(self.settings.voltage):
            self.setup(parameter=Parameter.VOLTAGE, value=voltage_value, channel_id=dac_index)

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Dummy method."""

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop outputing voltage."""
        self.device.set_dacs_zero()
        for dac_index in self.settings.dacs:
            channel = self.dac(dac_index=dac_index)
            logger.debug("Dac%d voltage resetted to  %f", dac_index, channel.voltage())

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        self.device.set_dacs_zero()
