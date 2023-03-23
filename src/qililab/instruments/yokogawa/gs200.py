"""
Class to interface with the voltage source Qblox S4g
"""
from dataclasses import dataclass

from qililab.instruments.current_source import CurrentSource
from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName
from qililab.typings import YokogawaGS200 as YokogawaGS200Driver
from qililab.typings.enums import Parameter


@InstrumentFactory.register
class GS200(CurrentSource):
    """Yokogawa GS200 class

    Args:
        name (InstrumentName): name of the instrument
        device (GS200): Instance of the qcodes GS200 class.
        settings (YokogawaGS200Settings): Settings of the instrument.
    """

    name = InstrumentName.YOKOGAWA_GS200

    @dataclass
    class YokogawaGS200Settings(CurrentSource.CurrentSourceSettings):
        """Contains the settings of a specific signal generator."""

    settings: YokogawaGS200Settings
    device: YokogawaGS200Driver

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set Qblox instrument calibration settings."""
        # TODO: write all other functionalities of this device
        if parameter.value == Parameter.CURRENT.value:
            self.device.current(value)
            return

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup."""
        self.device.source_mode("CURR")

    @Instrument.CheckDeviceInitialized
    def start(self):
        """Dummy method."""
        self.device.on()

        @Instrument.CheckDeviceInitialized
        def stop(self):
            """Stop outputing current."""
            self.device.off()
