"""
Class to interface with the voltage source Qblox D5a
"""
import string
from dataclasses import dataclass
from time import sleep
from typing import List
from xmlrpc.client import Boolean

from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.voltage_source import VoltageSource
from qililab.typings import InstrumentName, Parameter
from qililab.typings import QbloxD5a as QbloxD5aDriver


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

        # dacs_settings = [{"index": 0, "voltage": 0, "ramping_enabled": True, "ramp_rate":0.01, "span":"range_bi_max",},
        #                  {"index": 10, "voltage": 0, "ramping_enabled": True, "ramp_rate":0.01, "span":"range_bi_max",}]

    settings: QbloxD5aSettings
    device: QbloxD5aDriver

    @Instrument.CheckDeviceInitialized
    def setup(self):
        """Set D5a voltage and other settings."""
        self.device.dac0.span(self.span)
        self.device.dac0.ramping_enabled(self.ramping_enabled)
        self.device.dac0.ramp_rate(self.ramp_rate)
        self.device.dac0.voltage(self.voltage)
        while self.device.dac0.is_ramping():
            sleep(0.1)

        # for dac in self.dacs:
        #     self.get_dac(dac["index"]).voltage(dac[Parameter.VOLTAGE])
        #     self.get_dac(dac["index"]).ramping_enabled(dac[Parameter.RAMPING_ENABLED])
        #     # self.get_dac(dac["index"]).ramp_rate(dac["ramp_rate"]) ####
        #     # self.get_dac(dac["index"]).span(dac["span"]) ############################
        #     while self.get_dac(dac["index"]).is_ramping():
        #         sleep(0.1)
        # TODO: Implement more dacs

    # def get_dac(int) -> QbloxD5aDriver.Driver_D5aModule.D5aDacChannelNative:
    # TODO: Hint return type

    # def get_dac(self, dac_nr: int):
    #     """Returns the dac object corresponding to the given dac channel

    #     Args:
    #         dac_nr (int): dac channel number

    #     Returns:
    #         QbloxD5aDriver.Driver_D5aModule.D5aDacChannelNative: dac channel object
    #     """
    #     if dac_nr == 0:
    #         return self.device.dac0
    #     if dac_nr == 1:
    #         return self.device.dac1
    #     if dac_nr == 2:
    #         return self.device.dac2
    #     if dac_nr == 3:
    #         return self.device.dac3
    #     if dac_nr == 4:
    #         return self.device.dac4
    #     if dac_nr == 5:
    #         return self.device.dac5
    #     if dac_nr == 6:
    #         return self.device.dac6
    #     if dac_nr == 7:
    #         return self.device.dac7
    #     if dac_nr == 8:
    #         return self.device.dac8
    #     if dac_nr == 9:
    #         return self.device.dac9
    #     if dac_nr == 10:
    #         return self.device.dac10
    #     if dac_nr == 11:
    #         return self.device.dac11
    #     if dac_nr == 12:
    #         return self.device.dac12
    #     if dac_nr == 13:
    #         return self.device.dac13
    #     if dac_nr == 14:
    #         return self.device.dac14
    #     if dac_nr == 15:
    #         return self.device.dac15

    # @property
    # def dacs(self) -> List[dict]:
    #     return self.settings.dacs_settings

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup.
        For this instrument it is the same as a regular setup"""
        # self.setup()

    @Instrument.CheckDeviceInitialized
    def start(self):
        """Dummy method."""

    @Instrument.CheckDeviceInitialized
    def stop(self):
        """Stop outputing voltage."""
        # self.device.set_dacs_zero()

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        # self.device.set_dacs_zero()
