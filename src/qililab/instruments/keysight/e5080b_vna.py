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
    VNAFormatData,
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
        step_auto: bool | None = None
        step_size: float | None = None
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
        format_data: VNAFormatData | None = None
        format_border: VNAFormatBorder | None = None
        rf_on: bool | None = None

    settings: E5080BSettings
    device: KeysightE5080B
    device_initialized: bool = False

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
    def step_auto(self):
        """Sets and reads how the center frequency step size is set. When TRUE, center steps by 5% of span. When FALSE, center steps by STEP:SIZE value.
            Default is 40 Mhz. When STEP:AUTO is TRUE, this value is ignored.

        Returns:
            bool: settings.step_auto.
        """
        return self.settings.step_auto

    @property
    def step_size(self):
        """Sets the center frequency step size of the analyzer. This command sets the manual step size (only valid when STEP:AUTO is FALSE).

        Returns:
            float: settings.step_size.
        """
        return self.settings.step_size

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

        Returns:
            int: settings.points.
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
    def sweep_type(self) -> VNASweepTypes:
        """Sets the type of analyzer sweep mode. First set sweep type, then set sweep parameters such as frequency or power settings. Default is LIN

        Returns:
            Enum: settings.sweep_type.
        """
        return self.settings.sweep_type

    @property
    def sweep_mode(self) -> VNASweepModes:
        """Sets the number of trigger signals the specified channel will ACCEPT. Default is Continuous

        Returns:
            Enum: settings.sweep_mode.
        """
        return self.settings.sweep_mode

    @property
    def scattering_parameter(self) -> VNAScatteringParameters:
        """Sets the type of analyzer sweep mode. First set sweep type, then set sweep parameters such as frequency or power settings. Default is LIN

        Returns:
            Enum: settings.sweep_type.
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
    def averages_mode(self) -> VNAAverageModes:
        """Sets the type of averaging to perform: Point or Sweep (default is sweep).

        Returns:
            Enum: settings.averages_mode.
        """
        return self.settings.averages_mode

    @property
    def format_data(self) -> VNAFormatData:
        """Sets the data format for transferring measurement data and frequency data. Default is ASCii,0.

        Returns:
            Enum: settings.format_data.
        """
        return self.settings.format_data

    @property
    def rf_on(self):
        """Turns RF power from the source ON or OFF. Default is ON.

        Returns:
            bool: settings.rf_on
        """
        return self.settings.rf_on

    @property
    def format_border(self) -> VNAFormatBorder:
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

        if parameter == Parameter.STEP_AUTO:
            self.settings.step_auto = bool(value)
            if self.is_device_active():
                self.device.step_auto(self.step_auto)
            return

        if parameter == Parameter.STEP_SIZE:
            self.settings.step_size = float(value)
            if self.is_device_active():
                self.device.step_size(self.step_size)
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
            self.settings.sweep_type = value
            if self.is_device_active():
                self.device.sweep_type(self.sweep_type)
            return

        if parameter == Parameter.SWEEP_MODE:
            self.settings.sweep_mode = value
            if self.is_device_active():
                self.device.sweep_mode(self.sweep_mode)
            return

        if parameter == Parameter.SCATTERING_PARAMETER:
            self.settings.scattering_parameter = value
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
            self.settings.averages_mode = value
            if self.is_device_active():
                self.device.averages_mode(self.averages_mode)
            return

        if parameter == Parameter.FORMAT_DATA:
            self.settings.format_data = value
            if self.is_device_active():
                self.device.format_data(self.format_data)
            return

        if parameter == Parameter.RF_ON:
            self.settings.rf_on = value
            if self.is_device_active():
                self.device.rf_on(self.rf_on)
            return

        if parameter == Parameter.FORMAT_BORDER:
            self.settings.format_border = value
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
            return self.settings.frequency_start
        if parameter == Parameter.FREQUENCY_STOP:
            return self.settings.frequency_stop
        if parameter == Parameter.FREQUENCY_CENTER:
            return self.settings.frequency_center
        if parameter == Parameter.STEP_AUTO:
            return self.settings.step_auto
        if parameter == Parameter.STEP_SIZE:
            return self.settings.step_size
        if parameter == Parameter.FREQUENCY_SPAN:
            return self.settings.frequency_span
        if parameter == Parameter.CW_FREQUENCY:
            return self.settings.cw_frequency
        if parameter == Parameter.NUMBER_POINTS:
            return self.settings.number_points
        if parameter == Parameter.SOURCE_POWER:
            return self.settings.source_power
        if parameter == Parameter.IF_BANDWIDTH:
            return self.settings.if_bandwidth
        if parameter == Parameter.SWEEP_TYPE:
            return self.settings.sweep_type
        if parameter == Parameter.SWEEP_MODE:
            return self.settings.sweep_mode
        if parameter == Parameter.SCATTERING_PARAMETER:
            return self.settings.scattering_parameter
        if parameter == Parameter.AVERAGES_ENABLED:
            return self.settings.averages_enabled
        if parameter == Parameter.NUMBER_AVERAGES:
            return self.settings.number_averages
        if parameter == Parameter.AVERAGES_MODE:
            return self.settings.averages_mode
        if parameter == Parameter.FORMAT_DATA:
            return self.settings.format_data
        if parameter == Parameter.RF_ON:
            return self.settings.rf_on
        if parameter == Parameter.FORMAT_BORDER:
            return self.settings.format_border
        raise ParameterNotFound(self, parameter)

    def _get_trace(self):
        """Get the data of the current trace."""
        self.device.format_data("REAL,32")
        self.device.format_border("SWAPPED")  # SWAPPED is for IBM Compatible computers
        data = self.device.query_binary_values("CALC:MEAS:DATA:SDAT?")
        datareal = np.array(data[::2])  # Elements from data starting from 0 iterating by 2
        dataimag = np.array(data[1::2])  # Elements from data starting from 1 iterating by 2

        return datareal + 1j * dataimag

    def _pre_measurement(self):
        """
        Set everything needed for the measurement
        Averaging has to be enabled.
        """
        if not self.averages_enabled:
            self.device.averages_enabled(True)
            self.device.number_averages(1)

    def _start_measurement(self):
        """
        This function is called at the beginning of each single measurement in the spectroscopy script.
        Also, the averages need to be reset.
        """
        self.clear_averages()
        mode = self.settings.sweep_mode
        self.device.sweep_mode(mode)

    def _wait_for_averaging(self, timeout: int = DEFAULT_TIMEOUT):
        self.set_parameter(Parameter.AVERAGES_ENABLED, True)
        self.clear_averages()
        status_avg = int(self.device.ask("STAT:OPER:COND?"))
        start_time = time.time()

        while True:
            status_avg = int(self.device.ask("STAT:OPER:COND?"))
            if status_avg & (1 << 8):
                print("averages are done running")  #  to be removed once tested in HW
                break

            print("averages are still running")  #  to be removed once tested in HW
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout of {timeout} ms exceeded while waiting for averaging to complete.")
        return

    def read_tracedata(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Return the current trace data.
        It already releases the VNA after finishing the required number of averages.
        """
        self._pre_measurement()
        self._start_measurement()
        if self._wait_for_averaging(timeout):
            trace = self._get_trace()
            self.release()
            return trace
        return None

    def get_frequencies(self):
        """return freqpoints"""
        self.device.write("FORM:DATA:REAL,64")  # recommended to avoid frequency rounding errors
        return np.array(self.device.query("CALC:MEAS:X?"))

    def release(self):
        """Bring the VNA back to a mode where it can be easily used by the operator."""
        mode = VNASweepModes("cont")
        self.device.sweep_mode(mode)
        return

    def acquire_result(self, timeout: int = DEFAULT_TIMEOUT):
        """Convert the data received from the device to a Result object."""
        return VNAResult(data=self.read_tracedata(timeout))

    def initial_setup(self):
        self.device.format_data("REAL,32")
        self.device.cls()
        self.reset()
        self.device.source_power(self.source_power)
        self.device.sweep_type(self.sweep_type)
        self.device.sweep_mode(self.sweep_mode)
        self.device.points(self.points)
        self.device.if_bandwidth(self.if_bandwidth)
        self.device.scattering_parameter(self.scattering_parameter)
        self.device.rf_on(self.rf_on)
        self.device.averages_enabled(self.averages_enabled)
        self.device.step_auto(self.step_auto)

        if self.sweep_type != "SEGM":
            self.device.start_freq(self.start_freq)
            self.device.center_freq(self.center_freq)
            self.device.stop_freq(self.stop_freq)
            self.device.span(self.span)

        if self.sweep_type == "CW":
            self.device.cw(self.cw)

        if self.averages_enabled is True:
            self.device.averages_count(self.number_averages)
            self.device.averages_mode(self.averages_mode)

        if self.step_auto is False:
            self.device.step_size(self.step_size)

        self.device.format_data(self.format_data)
        self.device.format_border(self.format_border)

    def to_dict(self):
        """Return a dict representation of the VectorNetworkAnalyzer class."""
        return dict(super().to_dict().items())

    def clear_averages(self):
        self.device.clear_averages()

    @check_device_initialized
    def turn_on(self):
        """Turn on an instrument."""

    @check_device_initialized
    def turn_off(self):
        """Turn off an instrument."""

    @check_device_initialized
    def reset(self):
        """Reset instrument settings."""
        self.device.system_reset()
        self.device.opc()
