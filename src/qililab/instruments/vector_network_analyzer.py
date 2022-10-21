"""VectorNetworkAnalyzer class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument
from qililab.typings.enums import VNAScatteringParameters, VNATriggerModes
from qililab.typings.instruments.vector_network_analyzer import (
    VectorNetworkAnalyzerDriver,
)

DEFAULT_NUMBER_POINTS = 1000


class VectorNetworkAnalyzer(Instrument):
    """Abstract base class defining all vector network analyzers"""

    @dataclass
    class VectorNetworkAnalyzerSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator.

        Args:
            power (float): Power of the instrument. Value range is (-120, 25).
        """

        power: float
        scattering_parameter: VNAScatteringParameters = VNAScatteringParameters.S21
        frequency_span: float | None = None
        frequency_center: float | None = None
        frequency_start: float | None = None
        frequency_stop: float | None = None
        if_bandwidth: float | None = None
        averaging_enabled: bool = False
        number_averages: int = 1
        trigger_mode: VNATriggerModes = VNATriggerModes.INT
        number_points: int = DEFAULT_NUMBER_POINTS

    settings: VectorNetworkAnalyzerSettings
    device: VectorNetworkAnalyzerDriver

    @property
    def power(self):
        """VectorNetworkAnalyzer 'power' property.

        Returns:
            float: settings.power.
        """
        return self.settings.power

    @power.setter
    def power(self, value: float):
        """sets the power"""
        self.settings.power = value
        self.device.power(power=str(self.settings.power))

    @property
    def scattering_parameter(self):
        """VectorNetworkAnalyzer 'scattering_parameter' property.

        Returns:
            float: settings.scattering_parameter.
        """
        return self.settings.scattering_parameter.value

    @scattering_parameter.setter
    def scattering_parameter(self, value: str):
        """sets the scattering parameter"""
        self.settings.scattering_parameter = VNAScatteringParameters(value)
        self.device.scattering_parameter(par=self.settings.scattering_parameter.value)

    @property
    def frequency_span(self):
        """VectorNetworkAnalyzer 'frequency_span' property.

        Returns:
            float: settings.frequency_span.
        """
        return self.settings.frequency_span

    @frequency_span.setter
    def frequency_span(self, value: float):
        """sets the frequency span"""
        self.settings.frequency_span = value
        self.device.freq_span(freq=str(self.settings.frequency_span))

    @property
    def frequency_center(self):
        """VectorNetworkAnalyzer 'frequency_center' property.

        Returns:
            float: settings.frequency_center.
        """
        return self.settings.frequency_center

    @frequency_center.setter
    def frequency_center(self, value: float):
        """sets the frequency center"""
        self.settings.frequency_center = value
        self.device.freq_center(freq=str(self.settings.frequency_center))

    @property
    def frequency_start(self):
        """VectorNetworkAnalyzer 'frequency_start' property.

        Returns:
            float: settings.frequency_start.
        """
        return self.settings.frequency_start

    @frequency_start.setter
    def frequency_start(self, value: float):
        """sets the frequency start"""
        self.settings.frequency_start = value
        self.device.freq_start(freq=str(self.settings.frequency_start))

    @property
    def frequency_stop(self):
        """VectorNetworkAnalyzer 'frequency_stop' property.

        Returns:
            float: settings.frequency_stop.
        """
        return self.settings.frequency_stop

    @frequency_stop.setter
    def frequency_stop(self, value: float):
        """sets the frequency stop"""
        self.settings.frequency_stop = value
        self.device.freq_stop(freq=str(self.settings.frequency_stop))

    @property
    def if_bandwidth(self):
        """VectorNetworkAnalyzer 'if_bandwidth' property.

        Returns:
            float: settings.if_bandwidth.
        """
        return self.settings.if_bandwidth

    @if_bandwidth.setter
    def if_bandwidth(self, value: float):
        """sets the if bandwidth"""
        self.settings.if_bandwidth = value
        self.device.if_bandwidth(bandwidth=str(self.settings.if_bandwidth))

    @property
    def averaging_enabled(self):
        """VectorNetworkAnalyzer 'averaging_enabled' property.

        Returns:
            float: settings.averaging_enabled.
        """
        return self.settings.averaging_enabled

    @averaging_enabled.setter
    def averaging_enabled(self, value: bool):
        """sets the averaging enabled"""
        self.settings.averaging_enabled = value
        # TODO: verify the exact driver method to call
        # self.device.average_state(state=str(self.settings.averaging_enabled))

    @property
    def number_averages(self):
        """VectorNetworkAnalyzer 'number_averages' property.

        Returns:
            float: settings.number_averages.
        """
        return self.settings.number_averages

    @number_averages.setter
    def number_averages(self, value: int):
        """sets the number averages"""
        self.settings.number_averages = value
        self.device.average_count(count=str(self.settings.number_averages))

    @property
    def trigger_mode(self):
        """VectorNetworkAnalyzer 'trigger_mode' property.

        Returns:
            float: settings.trigger_mode.
        """
        return self.settings.trigger_mode.value

    @property
    def number_points(self):
        """VectorNetworkAnalyzer 'number_points' property.

        Returns:
            float: settings.number_points.
        """
        return self.settings.number_points

    @number_points.setter
    def number_points(self, value: int):
        """sets the number of points"""
        self.settings.number_points = value
        self.device.freq_npoints(points=str(self.settings.number_points))

    def to_dict(self):
        """Return a dict representation of the VectorNetworkAnalyzer class."""
        return dict(super().to_dict().items())

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Set initial instrument settings."""
        self.device.initial_setup()

    @Instrument.CheckDeviceInitialized
    def setup(self):
        """Set instrument settings."""

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument settings."""
        self.device.reset()

    @Instrument.CheckDeviceInitialized
    def stop(self):
        """Stop an instrument."""
        self.device.stop()

    def send_command(self, command: str) -> str:
        """send a command directly to the device"""
        return self.device.send_command(command=command, arg="")

    def read(self) -> str:
        """read directly from the device"""
        return self.device.read()

    def autoscale(self):
        """autoscale"""
        self.device.autoscale()

    def output(self, arg: str | int) -> str:
        """Turns RF output power on/off
        Give no argument to query current status.
        Parameters
        -----------
        arg : int, str
            Set state to 'ON', 'OFF', 1, 0
        """
        if isinstance(arg, (str, int)) and arg in ["ON", "OFF", 1, 0]:
            return self.device.output(arg=arg)
        raise ValueError("valid argument type must be either str or int and only valid values are ON, OFF, 1, 0")

    def electrical_delay(self, time: str):
        """Set electrical delay in 1
        example input: time = '100E-9' for 100ns"""
        self.device.electrical_delay(time=time)

    def get_data(self):
        """get data from device"""
        return self.device.get_data()
