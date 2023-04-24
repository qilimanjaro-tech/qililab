"""
Class to interface with the voltage source Qblox S4g
"""
from dataclasses import dataclass
from locale import currency

from qililab.instruments.current_source import CurrentSource
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName
from qililab.typings import YokogawaGS200 as YokogawaGS200Driver
from qililab.typings.enums import Parameter, YokogawaSourceModes


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

        output_status: bool
        current_value: float
        source_mode: YokogawaSourceModes = YokogawaSourceModes.CURR

    settings: YokogawaGS200Settings
    device: YokogawaGS200Driver

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (float | str | bool): new value
            channel_id (int | None): channel identifier of the parameter to update
        """
        if isinstance(value, str):
            self._set_parameter_str(parameter=parameter, value=value)
            return
        if isinstance(value, float):
            self._set_parameter_float(parameter=parameter, value=value)
            return

    def _set_parameter_str(self, parameter: Parameter, value: str):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (str): new value
        """
        if parameter == Parameter.SOURCE_MODE:
            self.source_mode = YokogawaSourceModes(value)
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter}")

    def _set_parameter_float(self, parameter: Parameter, value: float):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (float): new value
        """
        if parameter == Parameter.CURRENT_VALUE:
            self.current_value = value
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter}")

    @property
    def source_mode(self):
        """Yokogawa gs200 'source_mode' property.

        Returns:
            str: settings.source_mode.
        """
        return self.settings.source_mode

    @source_mode.setter
    def source_mode(self, value):
        """sets the source mode"""
        self.settings.source_mode = value
        self.device._set_source_mode(self.settings.source_mode.name)

    @property
    def output_status(self):
        """Yokogawa gs200 'output_status' property.

        Returns:
            bool: settings.output_status.
        """
        return self.settings.output_status

    @property
    def current_value(self):
        """Yokogawa gs200 'current_value' property.

        Returns:
            float: settings.current_value.
        """
        return self.settings.current_value

    @current_value.setter
    def current_value(self, value):
        """Sets the current_value"""
        self.settings.current_value = value
        self.device.ramp_current(value, abs(value), 0)

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup."""
        self.device._set_source_mode(YokogawaSourceModes.CURR.name)

    @Instrument.CheckDeviceInitialized
    def start(self):
        """Dummy method."""
        self.device.on()
        self.settings.output_status = True

    @Instrument.CheckDeviceInitialized
    def stop(self):
        """Stop outputing current."""
        self.device.off()
        self.settings.output_status = False

    def to_dict(self):
        """Return a dict representation of the VectorNetworkAnalyzer class."""
        return dict(super().to_dict().items())

    def ramp_current(self, ramp_to: float, step: float, delay: float) -> None:
        """Ramp current to a target value

        Args:
            ramp_to: float
                New target current value in Ampere
            step: float
                The ramp steps in Ampere
            delay: float
                The time between finishing one step and starting
                another in seconds.
        """
        self.settings.current_value = ramp_to
        self.device.ramp_current(ramp_to, step, delay)
