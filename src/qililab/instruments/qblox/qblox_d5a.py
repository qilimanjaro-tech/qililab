"""
Class to interface with the voltage source Qblox D5a
"""

from dataclasses import dataclass
from time import sleep
from typing import Any

from qililab.config import logger
from qililab.instruments.instrument import Instrument, ParameterNotFound
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

    device: QbloxD5aDriver

    def dac(self, dac_index: int):
        """get channel associated to the specific dac

        Args:
            dac_index (int): channel index

        Returns:
            _type_: _description_
        """
        return getattr(self.device, f"dac{dac_index}")

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set Qblox instrument calibration settings."""

        if channel_id is None:
            raise ValueError(f"channel not specified to update instrument {self.name.value}")
        if channel_id > 3:
            raise ValueError(
                f"the specified dac index:{channel_id} is out of range."
                + " Number of dacs is 4 -> maximum channel_id should be 3."
            )
        channel = self.dac(dac_index=channel_id)
        channel.set(parameter.value, value)
        self.parameters[parameter.value] = value

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup."""
        for dac in self.dacs:
            dac_index = dac.index
            for parameter, value in dac.parameters.items():
                self.device.dacs[dac_index].set(parameter, value)

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
