"""VectorNetworkAnalyzer class."""
from dataclasses import dataclass

from qililab.constants import DEFAULT_TIMEOUT
from qililab.instruments.instrument import Instrument
from qililab.result.vna_result import VNAResult
from qililab.typings.enums import (
    Parameter,
    VNAScatteringParameters,
    VNASweepModes,
    VNATriggerModes,
)
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
        sweep_mode: VNASweepModes = VNASweepModes.CONT
        device_timeout: float = DEFAULT_TIMEOUT
        electrical_delay: float = 0.0

    settings: VectorNetworkAnalyzerSettings
    device: VectorNetworkAnalyzerDriver

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
        if isinstance(value, bool):
            self._set_parameter_bool(parameter=parameter, value=value)
            return
        if isinstance(value, float):
            self._set_parameter_float(parameter=parameter, value=value)
            return
        if isinstance(value, int):
            self._set_parameter_int(parameter=parameter, value=value)
            return
        raise ValueError(f"Invalid Parameter: {parameter} with type {type(parameter)}")

    def _set_parameter_str(self, parameter: Parameter, value: str):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (str): new value
        """
        if parameter == Parameter.SCATTERING_PARAMETER:
            self.scattering_parameter = value
            return
        if parameter == Parameter.TRIGGER_MODE:
            self.settings.trigger_mode = VNATriggerModes(value)
            return
        if parameter == Parameter.SWEEP_MODE:
            self.settings.sweep_mode = VNASweepModes(value)
            return

        raise ValueError(f"Invalid Parameter: {parameter}")

    def _set_parameter_bool(self, parameter: Parameter, value: bool):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (bool): new value
        """
        if parameter == Parameter.AVERAGING_ENABLED:
            self.averaging_enabled = value
            return

        raise ValueError(f"Invalid Parameter: {parameter}")

    def _set_parameter_float(
        self,
        parameter: Parameter,
        value: float,
    ):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (float): new value
        """

        if parameter == Parameter.POWER:
            self.power = value
            return
        if parameter == Parameter.FREQUENCY_SPAN:
            self.frequency_span = value
            return
        if parameter == Parameter.FREQUENCY_CENTER:
            self.frequency_center = value
            return
        if parameter == Parameter.FREQUENCY_START:
            self.frequency_start = value
            return
        if parameter == Parameter.FREQUENCY_STOP:
            self.frequency_stop = value
            return
        if parameter == Parameter.IF_BANDWIDTH:
            self.if_bandwidth = value
            return
        if parameter == Parameter.DEVICE_TIMEOUT:
            self.device_timeout = value
            return
        if parameter == Parameter.ELECTRICAL_DELAY:
            self.electrical_delay = value
            return

        raise ValueError(f"Invalid Parameter: {parameter}")

    def _set_parameter_int(self, parameter: Parameter, value: int):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (int): new value
        """

        if parameter == Parameter.NUMBER_AVERAGES:
            self.number_averages = value
            return

        if parameter == Parameter.NUMBER_POINTS:
            self.number_points = value
            return

        raise ValueError(f"Invalid Parameter: {parameter}")

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
        self.device.power(power=f"{self.settings.power:.1f}")

    @property
    def scattering_parameter(self):
        """VectorNetworkAnalyzer 'scattering_parameter' property.

        Returns:
            str: settings.scattering_parameter.
        """
        return self.settings.scattering_parameter

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
            bool: settings.averaging_enabled.
        """
        return self.settings.averaging_enabled

    @averaging_enabled.setter
    def averaging_enabled(self, value: bool):
        """sets the averaging enabled"""
        self.settings.averaging_enabled = value
        self.device.average_state(state=self.settings.averaging_enabled)

    @property
    def number_averages(self):
        """VectorNetworkAnalyzer 'number_averages' property.

        Returns:
            int: settings.number_averages.
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
            str: settings.trigger_mode.
        """
        return self.settings.trigger_mode

    @property
    def number_points(self):
        """VectorNetworkAnalyzer 'number_points' property.

        Returns:
            int: settings.number_points.
        """
        return self.settings.number_points

    @number_points.setter
    def number_points(self, value: int):
        """sets the number of points"""
        self.settings.number_points = value
        self.device.freq_npoints(points=str(self.settings.number_points))

    @property
    def sweep_mode(self):
        """VectorNetworkAnalyzer'sweep_mode' property.

        Returns:
            str: settings.sweep_mode.
        """
        return self.settings.sweep_mode

    @sweep_mode.setter
    def sweep_mode(self, value: str):
        """sets the sweep mode"""
        self.settings.sweep_mode = VNASweepModes(value)
        self.device.set_sweep_mode(mode=self.settings.sweep_mode.value)

    @property
    def device_timeout(self):
        """VectorNetworkAnalyzer 'device_timeout' property.

        Returns:
            float: settings.device_timeout.
        """
        return self.settings.device_timeout

    @device_timeout.setter
    def device_timeout(self, value: float):
        """sets the device timeout in mili seconds"""
        self.settings.device_timeout = value
        self.device.set_timeout(value=self.settings.device_timeout)

    @property
    def electrical_delay(self):
        """VectorNetworkAnalyzer 'electrical_delay' property.

        Returns:
            float: settings.electrical_delay.
        """
        return self.settings.electrical_delay

    @electrical_delay.setter
    def electrical_delay(self, value: float):
        """sets the electrical delay"""
        self.settings.electrical_delay = value
        self.device.electrical_delay(etime=f"{self.settings.electrical_delay:.12f}")

    def to_dict(self):
        """Return a dict representation of the VectorNetworkAnalyzer class."""
        return dict(super().to_dict().items())

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Set initial instrument settings."""
        self.device.initial_setup()

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument settings."""
        self.device.reset()

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Start an instrument."""
        self.device.start()

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop an instrument."""
        self.device.stop()

    def send_command(self, command: str) -> str:
        """Send a command directly to the device."""
        return self.device.send_command(command=command, arg="")

    def autoscale(self):
        """Autoscale."""
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

    def average_clear(self, channel=1):
        """Clears the average buffer."""
        self.device.average_clear(channel=channel)

    def get_frequencies(self):
        """return freqpoints"""
        return self.device.get_freqs()

    def ready(self) -> bool:
        """
        This is a proxy function.
        Returns True if the VNA is on HOLD after finishing the required number of averages.
        """
        return self.device.ready()

    def release(self):
        """Bring the VNA back to a mode where it can be easily used by the operator."""
        self.settings.sweep_mode = VNASweepModes("cont")
        self.device.release()

    def read_tracedata(self):
        """Get data from device."""
        return self.device.read_tracedata()

    def acquire_result(self):
        """Convert the data received from the device to a Result object."""
        return VNAResult(data=self.device.read_tracedata())
