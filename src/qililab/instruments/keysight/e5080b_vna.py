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

"""KeySight Vector Network Analyzer E5080B class."""

import time
from dataclasses import dataclass
from typing import cast

import numpy as np

from qililab.constants import DEFAULT_TIMEOUT
from qililab.instruments.decorators import check_device_initialized, log_set_parameter
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.result.vna_result import VNAResult
from qililab.typings import ChannelID, InstrumentName, Parameter, ParameterValue
from qililab.typings.enums import (
    VNAAverageModes,
    VNAFormatBorder,
    VNAScatteringParameters,
    VNASweepModes,
    VNASweepTypes,
)
from qililab.typings.instruments.keysight_e5080b import KeysightE5080B


@InstrumentFactory.register
class E5080B(Instrument):
    """KeySight Vector Network Analyzer E5080B"""

    name = InstrumentName.KEYSIGHT_E5080B
    timeout: int = DEFAULT_TIMEOUT

    @dataclass
    class E5080BSettings(Instrument.InstrumentSettings):
        """Contains the settings of the VNA.

        Args:
            power (float): Output power in dBm.
            start_freq (float): Start frequency in Hz.
            stop_freq (float): Stop frequency in Hz.
            num_points (int): Number of measurement points.
            if_bandwidth (float): Intermediate frequency bandwidth.
        """

        frequency_start: float | None = None
        frequency_stop: float | None = None
        frequency_center: float | None = None
        frequency_span: float | None = None
        cw_frequency: float | None = None
        number_points: int | None = None
        source_power: float | None = None
        if_bandwidth: float | None = None
        sweep_type: VNASweepTypes | None = None
        sweep_mode: VNASweepModes | None = None
        averages_enabled: bool | None = None
        number_averages: int | None = None
        averages_mode: VNAAverageModes | None = None
        scattering_parameter: VNAScatteringParameters | None = None
        format_border: VNAFormatBorder | None = None
        rf_on: bool | None = None

    settings: E5080BSettings
    device: KeysightE5080B

    @property
    def start_freq(self):
        """Sets the start frequency of the analyzer.

        Returns:
            float: settings.start_freq.
        """
        return self.settings.frequency_start

    @property
    def stop_freq(self):
        """Sets the stop frequency of the analyzer.

        Returns:
            float: settings.stop_freq.
        """
        return self.settings.frequency_stop

    @property
    def center_freq(self):
        """Sets the center frequency of the analyzer.

        Returns:
            float: settings.center_freq.
        """
        return self.settings.frequency_center

    @property
    def span(self):
        """Sets the frequency span of the analyzer.

        Returns:
            float: settings.span.
        """
        return self.settings.frequency_span

    @property
    def cw(self):
        """Sets the Continuous Wave (or Fixed) frequency. Must also send SENS:SWEEP:TYPE CW to put the analyzer into CW sweep mode.

        Returns:
            float: settings.cw.
        """
        return self.settings.cw_frequency

    @property
    def points(self):
        """Sets the number of data points for the measurement.
        REQ THE VNA TO BE RESETTED IF USING SET_PARAMETER IF VALUE IS CHANGED

        Returns:
            int: settings.number_points.
        """
        return self.settings.number_points

    @property
    def source_power(self):
        """Sets the RF power output level.

        Returns:
            float: settings.source_power.
        """
        return self.settings.source_power

    @property
    def if_bandwidth(self):
        """Sets the bandwidth of the digital IF filter to be used in the measurement.

        Returns:
            float: settings.if_bandwidth.
        """
        return self.settings.if_bandwidth

    @property
    def sweep_type(self) -> VNASweepTypes | None:
        """Sets the type of analyzer sweep mode. First set sweep type, then set sweep parameters such as frequency or power settings. Default is LIN

        Returns:
            Enum: settings.sweep_type.
        """
        return self.settings.sweep_type

    @property
    def sweep_mode(self) -> VNASweepModes | None:
        """Sets the number of trigger signals the specified channel will ACCEPT. Default is Continuous

        Returns:
            Enum: settings.sweep_mode.
        """
        return self.settings.sweep_mode

    @property
    def scattering_parameter(self) -> VNAScatteringParameters | None:
        """Set/get a measurement parameter for the specified measurement.

        Returns:
            Enum: settings.scattering_parameter.
        """
        return self.settings.scattering_parameter

    @property
    def averages_enabled(self):
        """Turns trace averaging ON or OFF.

        Returns:
            bool: settings.averages_enabled.
        """
        return self.settings.averages_enabled

    @property
    def number_averages(self):
        """Sets the number of measurements to combine for an average. Must also set SENS:AVER[:STATe] ON

        Returns:
            int: settings.number_averages.
        """
        return self.settings.number_averages

    @property
    def averages_mode(self) -> VNAAverageModes | None:
        """Sets the type of averaging to perform: Point or Sweep (default is sweep).

        Returns:
            Enum: settings.averages_mode.
        """
        return self.settings.averages_mode

    @property
    def rf_on(self):
        """Turns RF power from the source ON or OFF. Default is ON.

        Returns:
            bool: settings.rf_on
        """
        return self.settings.rf_on

    @property
    def format_border(self) -> VNAFormatBorder | None:
        """Set the byte order used for GPIB data transfer. Some computers read data from the analyzer in the reverse order.
            This command is only implemented if FORMAT:DATA is set to :REAL.

        Returns:
            Enum: settings.format_border.
        """
        return self.settings.format_border

    @log_set_parameter
    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None):
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int): Channel identifier of the parameter to update.
            port (int): Port identifier of the parameter to update.
        """

        if parameter == Parameter.FREQUENCY_START:
            self.settings.frequency_start = float(value)
            if self.is_device_active():
                self.device.start_freq(self.start_freq)
            return

        if parameter == Parameter.FREQUENCY_STOP:
            self.settings.frequency_stop = float(value)
            if self.is_device_active():
                self.device.stop_freq(self.stop_freq)
            return

        if parameter == Parameter.FREQUENCY_CENTER:
            self.settings.frequency_center = float(value)
            if self.is_device_active():
                self.device.center_freq(self.center_freq)
            return

        if parameter == Parameter.FREQUENCY_SPAN:
            self.settings.frequency_span = float(value)
            if self.is_device_active():
                self.device.span(self.span)
            return

        if parameter == Parameter.CW_FREQUENCY:
            self.settings.cw_frequency = float(value)
            if self.is_device_active():
                self.device.cw(self.cw)
            return

        if parameter == Parameter.NUMBER_POINTS:
            self.settings.number_points = int(value)
            if self.is_device_active():
                self.device.points(self.points)
            return

        if parameter == Parameter.SOURCE_POWER:
            self.settings.source_power = float(value)
            if self.is_device_active():
                self.device.source_power(self.source_power)
            return

        if parameter == Parameter.IF_BANDWIDTH:
            self.settings.if_bandwidth = float(value)
            if self.is_device_active():
                self.device.if_bandwidth(self.if_bandwidth)
            return

        if parameter == Parameter.SWEEP_TYPE:
            self.settings.sweep_type = VNASweepTypes(value)
            if self.is_device_active():
                self.device.sweep_type(self.sweep_type)
            return

        if parameter == Parameter.SWEEP_MODE:
            self.settings.sweep_mode = VNASweepModes(value)
            if self.is_device_active():
                self.device.sweep_mode(self.sweep_mode)
            return

        if parameter == Parameter.SCATTERING_PARAMETER:
            self.settings.scattering_parameter = VNAScatteringParameters(value)
            if self.is_device_active():
                self.device.scattering_parameter(self.scattering_parameter)
            return

        if parameter == Parameter.AVERAGES_ENABLED:
            self.settings.averages_enabled = bool(value)
            if self.is_device_active():
                self.device.averages_enabled(self.averages_enabled)
            return

        if parameter == Parameter.NUMBER_AVERAGES:
            self.settings.number_averages = int(value)
            if self.is_device_active():
                self.device.averages_count(self.number_averages)
            return

        if parameter == Parameter.AVERAGES_MODE:
            self.settings.averages_mode = VNAAverageModes(value)
            if self.is_device_active():
                self.device.averages_mode(self.averages_mode)
            return

        if parameter == Parameter.RF_ON:
            self.settings.rf_on = bool(value)
            if self.is_device_active():
                self.device.rf_on(self.rf_on)
            return

        if parameter == Parameter.FORMAT_BORDER:
            self.settings.format_border = VNAFormatBorder(value)
            if self.is_device_active():
                self.device.format_border(self.format_border)
            return

        raise ParameterNotFound(self, parameter)

    def get_parameter(self, parameter: Parameter, channel_id: ChannelID | None = None) -> ParameterValue:
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
        """

        if parameter == Parameter.FREQUENCY_START:
            self.settings.frequency_start = self.device.start_freq.get()
            return cast("ParameterValue", self.settings.frequency_start)
        
        if parameter == Parameter.FREQUENCY_STOP:
            self.settings.frequency_stop = self.device.stop_freq.get()
            return cast("ParameterValue", self.settings.frequency_stop)
        
        if parameter == Parameter.FREQUENCY_CENTER:
            self.settings.frequency_center = self.device.center_freq.get()
            return cast("ParameterValue", self.settings.frequency_center)
        
        if parameter == Parameter.FREQUENCY_SPAN:
            self.settings.frequency_span = self.device.span.get()
            return cast("ParameterValue", self.settings.frequency_span)
        
        if parameter == Parameter.CW_FREQUENCY:
            self.settings.cw_frequency = self.device.cw.get()
            return cast("ParameterValue", self.settings.cw_frequency)
        
        if parameter == Parameter.NUMBER_POINTS:
            self.settings.number_points = self.device.points.get()
            return cast("ParameterValue", self.settings.number_points)
        
        if parameter == Parameter.SOURCE_POWER:
            self.settings.source_power = self.device.source_power.get()
            return cast("ParameterValue", self.settings.source_power)
        
        if parameter == Parameter.IF_BANDWIDTH:
            self.settings.if_bandwidth = self.device.if_bandwidth.get()
            return cast("ParameterValue", self.settings.if_bandwidth)
        
        if parameter == Parameter.SWEEP_TYPE:
            self.settings.sweep_type = self.device.sweep_type.get().strip('"').strip()
            return cast("ParameterValue", self.settings.sweep_type)
        
        if parameter == Parameter.SWEEP_MODE:
            self.settings.sweep_mode = self.device.sweep_mode.get().strip('"').strip()
            return cast("ParameterValue", self.settings.sweep_mode)
        
        if parameter == Parameter.SCATTERING_PARAMETER:
            self.settings.scattering_parameter = self.device.scattering_parameter.get().strip('"').strip()
            return cast("ParameterValue", self.settings.scattering_parameter)
        
        if parameter == Parameter.AVERAGES_ENABLED:
            self.settings.averages_enabled = self.device.averages_enabled.get()
            return cast("ParameterValue", self.settings.averages_enabled)
        
        if parameter == Parameter.NUMBER_AVERAGES:
            self.settings.number_averages = self.device.averages_count.get()
            return cast("ParameterValue", self.settings.number_averages)
        
        if parameter == Parameter.AVERAGES_MODE:
            self.settings.averages_mode = self.device.averages_mode.get().strip('"').strip()
            return cast("ParameterValue", self.settings.averages_mode)
        
        if parameter == Parameter.RF_ON:
            self.settings.rf_on = self.device.rf_on.get()
            return cast("ParameterValue", self.settings.rf_on)
        
        if parameter == Parameter.FORMAT_BORDER:
            self.settings.format_border = self.device.format_border.get().strip('"').strip()
            return cast("ParameterValue", self.settings.format_border)
        
        raise ParameterNotFound(self, parameter)

    def _get_trace(self):
        """Get the data of the current trace."""
        self.device.format_data("REAL,32")
        self.device.format_border("SWAP")  # SWAPPED is for IBM Compatible computers
        data = self.device.visa_handle.query_binary_values("CALC:MEAS:DATA:SDAT?")
        datareal = np.array(data[::2])  # Elements from data starting from 0 iterating by 2
        dataimag = np.array(data[1::2])  # Elements from data starting from 1 iterating by 2

        return datareal + 1j * dataimag

    def _wait_for_averaging(self, timeout: int = DEFAULT_TIMEOUT):
        number_averages = self.get_parameter(Parameter.NUMBER_AVERAGES)
        self.set_parameter(Parameter.AVERAGES_ENABLED, True)
        self.clear_averages()
        start_time = time.time()
        while True:
            time.sleep(0.5)
            status_avg = int(self.device.ask("STAT:OPER:COND?"))
            if status_avg & (1 << 8) and number_averages > 1:
                break
            elif status_avg & (1 << 10) and number_averages == 1:
                break
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout of {timeout} ms exceeded while waiting for averaging to complete.")
        return

    def read_tracedata(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Return the current data.
        It already releases the VNA after finishing the required number of averages.
        """
        time.sleep(5)
        self.cls()
        self._wait_for_averaging(timeout)
        trace = self._get_trace()
        self.release()
        return trace

    def get_frequencies(self):
        """return freqpoints"""
        self.device.write("FORM:DATA:REAL,64")  # recommended to avoid frequency rounding errors
        return np.array(self.device.visa_handle.query_binary_values("CALC:MEAS:X?"))

    def release(self):
        """Bring the VNA back to a mode where it can be easily used by the operator."""
        mode = "CONT"
        self.device.sweep_mode(mode)
        return

    def acquire_result(self, timeout: int = DEFAULT_TIMEOUT):
        """Convert the data received from the device to a Result object."""
        return VNAResult(data=self.read_tracedata(timeout))

    def initial_setup(self):
        self.device.format_data("REAL,32")
        self.cls()
        if self.settings.sweep_type is not None:
            self.device.sweep_type(self.settings.sweep_type)
        if self.settings.sweep_mode is not None:
            self.device.sweep_mode(self.settings.sweep_mode)
        if self.settings.number_points is not None:
            self.device.points(self.settings.number_points)
        if self.settings.if_bandwidth is not None:
            self.device.if_bandwidth(self.settings.if_bandwidth)
        if self.settings.scattering_parameter is not None:
            self.device.scattering_parameter(self.scattering_parameter)
        if self.settings.format_border is not None:
            self.device.format_border(self.settings.format_border)

        if self.settings.sweep_type != VNASweepTypes.SEGM:
            if self.settings.frequency_start is not None:
                self.device.start_freq(self.settings.frequency_start)
            if self.settings.frequency_center is not None:
                self.device.center_freq(self.settings.frequency_center)
            if self.settings.frequency_stop is not None:
                self.device.stop_freq(self.settings.frequency_stop)
            if self.settings.frequency_span is not None:
                self.device.span(self.settings.frequency_span)

        if self.settings.sweep_type == VNASweepTypes.CW and self.settings.cw_frequency is not None:
            self.device.cw(self.settings.cw_frequency)
        if self.settings.number_averages is not None:
            self.device.averages_count(self.settings.number_averages)
        if self.settings.averages_mode is not None:
            self.device.averages_mode(self.settings.averages_mode)
        if self.settings.source_power is not None:
            self.device.source_power(self.settings.source_power)
        if self.settings.rf_on is not None:
            self.device.rf_on(self.settings.rf_on)

    def to_dict(self):
        """Return a dict representation of the VectorNetworkAnalyzer class."""
        return dict(super().to_dict().items())

    def cls(self):
        """Clear Status."""
        self.device.cls()

    def opc(self):
        """Operation complete command."""
        self.device.opc()

    def clear_averages(self):
        """Restart averages."""
        self.device.clear_averages()

    @check_device_initialized
    def turn_on(self):
        """Turn on an instrument."""

    @check_device_initialized
    def turn_off(self):
        """Turn off an instrument."""

    @check_device_initialized
    def reset(self):
        """The wrapper doesn't allow a reset for this instrument"""
