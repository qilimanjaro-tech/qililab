# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""VectorNetworkAnalyzer class."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.typings.enums import Parameter, VNAScatteringParameters, VNATriggerModes
from qililab.typings.instruments.vector_network_analyzer import VectorNetworkAnalyzerDriver

DEFAULT_NUMBER_POINTS = 1000


class VectorNetworkAnalyzer(Instrument, ABC):  # pylint: disable=too-many-instance-attributes, too-many-public-methods
    """Abstract base class defining all vector network analyzers"""

    @dataclass
    class VectorNetworkAnalyzerSettings(Instrument.InstrumentSettings):  # pylint: disable=too-many-instance-attributes
        """Contains the settings of a specific signal generator.

        Args:
            power (float): Power of the instrument in dBm
            scatering_parameter (str): Scatering parameter of the instrument
            frequency_span (float): Frequency span of the instrument in KHz
            frequency_center (float): Frequency center of the instrument in Hz
            frequency_start (float): Frequency start of the instrument in Hz
            frequency_stop (float): Frequency stop of the instrument in Hz
            if_bandwidth (float): Bandwidth of the instrument in Hz
            averaging_enabled (bool): Whether averaging is enabled or not in the instrument
            trigger_mode (str): Trigger mode of the instrument
            number_points (int): Number of points for sweep
            device_timeout (float): Timeout of the instrument in ms
            electrical_delay (float): Electrical delay of the instrument in s
        """

        power: float
        scattering_parameter: VNAScatteringParameters = VNAScatteringParameters.S11
        frequency_span: float | None = None
        frequency_center: float | None = None
        frequency_start: float | None = None
        frequency_stop: float | None = None
        if_bandwidth: float | None = None
        averaging_enabled: bool = False
        number_averages: int = 1
        trigger_mode: VNATriggerModes = VNATriggerModes.INT
        number_points: int = DEFAULT_NUMBER_POINTS
        electrical_delay: float = 0.0

    settings: VectorNetworkAnalyzerSettings
    device: VectorNetworkAnalyzerDriver

    def setup(self, parameter: Parameter, value: float | str | bool | int, channel_id: int | None = None):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (float | str | bool | int): new value
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
        raise ParameterNotFound(f"Invalid Parameter: {parameter} with type {type(parameter)}")

    def _set_parameter_str(self, parameter: Parameter, value: str):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (str): new value
        """
        if parameter == Parameter.SCATTERING_PARAMETER:
            self.scattering_parameter = VNAScatteringParameters(value)
            return
        if parameter == Parameter.TRIGGER_MODE:
            self.settings.trigger_mode = VNATriggerModes(value)
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter}")

    def _set_parameter_bool(self, parameter: Parameter, value: bool):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (bool): new value
        """
        if parameter == Parameter.AVERAGING_ENABLED:
            self.averaging_enabled = value
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter}")

    def _set_parameter_float(  # pylint: disable=too-many-branches, too-many-return-statements
        self, parameter: Parameter, value: float
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
        if parameter == Parameter.ELECTRICAL_DELAY:
            self.electrical_delay = value
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter}")

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

        raise ParameterNotFound(f"Invalid Parameter: {parameter}")

    @property
    def power(self):
        """VectorNetworkAnalyzer 'power' property.

        Returns:
            float: settings.power
        """
        return self.settings.power

    @power.setter
    @abstractmethod
    def power(self, value: float, channel=1, port=1):
        """sets the power in dBm"""

    @property
    def scattering_parameter(self):
        """VectorNetworkAnalyzer 'scattering_parameter' property.

        Returns:
            str: settings.scattering_parameter.
        """
        return self.settings.scattering_parameter

    @scattering_parameter.setter
    def scattering_parameter(self, value: str, channel=1):
        """sets the scattering parameter"""
        self.settings.scattering_parameter = VNAScatteringParameters(value)

        if self.is_device_active():
            scat_par = self.settings.scattering_parameter.value
            self.send_command(f"CALC1:MEAS{channel}:PAR", scat_par)

    @property
    def frequency_span(self):
        """VectorNetworkAnalyzer 'frequency_span' property.

        Returns:
            float: settings.frequency_span.
        """
        return self.settings.frequency_span

    @frequency_span.setter
    def frequency_span(self, value: float, channel=1):
        """sets the frequency span in kHz"""
        self.settings.frequency_span = value

        if self.is_device_active():
            freq = str(self.settings.frequency_span)
            self.send_command(f"SENS{channel}:FREQ:SPAN", freq)

    @property
    def frequency_center(self):
        """VectorNetworkAnalyzer 'frequency_center' property.

        Returns:
            float: settings.frequency_center.
        """
        return self.settings.frequency_center

    @frequency_center.setter
    def frequency_center(self, value: float, channel=1):
        """sets the frequency center in Hz"""
        self.settings.frequency_center = value

        if self.is_device_active():
            freq = str(self.settings.frequency_center)
            self.send_command(f"SENS{channel}:FREQ:CENT", freq)

    @property
    def frequency_start(self):
        """VectorNetworkAnalyzer 'frequency_start' property.

        Returns:
            float: settings.frequency_start.
        """
        return self.settings.frequency_start

    @frequency_start.setter
    def frequency_start(self, value: float, channel=1):
        """sets the frequency start in Hz"""
        self.settings.frequency_start = value

        if self.is_device_active():
            freq = str(self.settings.frequency_start)
            self.send_command(f"SENS{channel}:FREQ:STAR", freq)

    @property
    def frequency_stop(self):
        """VectorNetworkAnalyzer 'frequency_stop' property.

        Returns:
            float: settings.frequency_stop.
        """
        return self.settings.frequency_stop

    @frequency_stop.setter
    def frequency_stop(self, value: float, channel=1):
        """sets the frequency stop in Hz"""
        self.settings.frequency_stop = value

        if self.is_device_active():
            freq = str(self.settings.frequency_stop)
            self.send_command(f"SENS{channel}:FREQ:STOP", freq)

    @property
    def if_bandwidth(self):
        """VectorNetworkAnalyzer 'if_bandwidth' property.

        Returns:
            float: settings.if_bandwidth.
        """
        return self.settings.if_bandwidth

    @if_bandwidth.setter
    @abstractmethod
    def if_bandwidth(self, value: float, channel=1):
        """sets the if bandwidth in Hz"""

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

        if self.is_device_active():
            self._average_state(state=self.settings.averaging_enabled)

    @property
    def number_averages(self):
        """VectorNetworkAnalyzer 'number_averages' property.

        Returns:
            int: settings.number_averages.
        """
        return self.settings.number_averages

    @number_averages.setter
    def number_averages(self, value: int, channel=1):
        """sets the number averages"""
        self.settings.number_averages = value

        if self.is_device_active():
            self._average_count(count=str(self.settings.number_averages), channel=channel)

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
    def number_points(self, value: int, channel=1):
        """sets the number of points for sweep"""
        self.settings.number_points = value

        if self.is_device_active():
            points = str(self.settings.number_points)
            self.send_command(f":SENS{channel}:SWE:POIN", points)

    @property
    def electrical_delay(self):
        """VectorNetworkAnalyzer 'electrical_delay' property.

        Returns:
            float: settings.electrical_delay.
        """
        return self.settings.electrical_delay

    @electrical_delay.setter
    @abstractmethod
    def electrical_delay(self, value: float):
        """
        Set electrical delay in channel 1

        Input:
            value (str) : Electrical delay in ns
                example: value = '100E-9' for 100ns
        """

    def _average_state(self, state, channel=1):
        """Set status of Average."""
        if state:
            self.send_command(f"SENS{channel}:AVER:STAT", "ON")
        else:
            self.send_command(f"SENS{channel}:AVER:STAT", "OFF")

    def _average_count(self, count, channel):
        """Set the average count"""
        self.send_command(f"SENS{channel}:AVER:COUN", count)
        self.send_command(command=f":SENS{channel}:AVER:CLE", arg="")

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
        return self.send_command(command=":OUTP", arg="ON")

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop an instrument."""
        return self.send_command(command=":OUTP", arg="OFF")

    def send_command(self, command: str, arg: str = "?") -> str:
        """Send a command directly to the device.

        Args:
            command(str): Command to send the device
            arg(str): Argument to send the command with. Default empty string

        Example:
            >>> send_command(command=":OUTP",arg="ON") -> ":OUTP ON"
        """
        return self.device.send_command(command=command, arg=arg)

    def send_query(self, query: str):
        """
        Send a query directly to the device.

        Input:
            query(str): Query to send the device
        """
        return self.device.send_query(query)

    def send_binary_query(self, query: str):
        """
        Send a binary query directly to the device.

        Input:
            query(str): Query to send the device
        """
        return self.device.send_binary_query(query)

    def autoscale(self):
        """Autoscale"""
        self.send_command(command="DISP:WIND:TRAC:Y:AUTO", arg="")

    def read(self) -> str:
        """Read directly from the device"""
        return self.device.read()

    def read_raw(self) -> str:
        """Read raw data directly from the device"""
        return self.device.read_raw()

    def set_timeout(self, value: float):
        """Set timeout in mili seconds"""
        self.device.set_timeout(value)
