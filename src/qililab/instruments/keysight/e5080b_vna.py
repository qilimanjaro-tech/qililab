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
from qililab.instruments.decorators import log_set_parameter
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.result.vna_result import VNAResult
from qililab.typings import ChannelID, InstrumentName, Parameter, ParameterValue
from qililab.typings.enums import VNASweepModes
from qililab.typings.instruments.keysight_e5080b import KeysightE5080B


@InstrumentFactory.register
class E5080B(Instrument):
    """KeySight Vector Network Analyzer E5080B"""

    name = InstrumentName.KEYSIGHT_E5080B

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
        
        power: float
        start_freq: float
        stop_freq: float
        center_freq: float
        step_auto: bool
        step_size: float
        span: float
        cw: float
        points: int
        if_bandwidth: float
        sweep_type: Enum
        averages_enabled: bool
        averages_count: int
        averages_mode: Enum
        

    settings: E5080BSettings
    device: KeysightE5080B
    device_initialized: bool = False

    @property
    def start_freq(self):
        """Sets the start frequency of the analyzer.

        Returns:
            float: settings.start_freq.
        """
        return self.settings.start_freq
    
    @property
    def stop_freq(self):
        """Sets the stop frequency of the analyzer.

        Returns:
            float: settings.stop_freq.
        """
        return self.settings.stop_freq

    @property
    def center_freq(self):
        """Sets the center frequency of the analyzer.

        Returns:
            float: settings.center_freq.
        """
        return self.settings.center_freq
    
    @property
    def step_auto(self):
        """ Sets and reads how the center frequency step size is set. When TRUE, center steps by 5% of span. When FALSE, center steps by STEP:SIZE value.
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
        return self.settings.span
    
    @property
    def cw(self):
        """Sets the Continuous Wave (or Fixed) frequency. Must also send SENS:SWEEP:TYPE CW to put the analyzer into CW sweep mode.

        Returns:
            float: settings.cw.
        """
        return self.settings.cw

    @property
    def points(self):
        """Sets the number of data points for the measurement.

        Returns:
            int: settings.points.
        """
        return self.settings.points
    
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
    def sweep_type(self):
        """Sets the type of analyzer sweep mode. First set sweep type, then set sweep parameters such as frequency or power settings. Default is LIN

        Returns:
            Enum: settings.sweep_type.
        """
        return self.settings.sweep_type

    @property
    # TODO:def MEASURE TO BE ADDED

    @property
    def averages_enabled(self):
        """Turns trace averaging ON or OFF.

        Returns:
            bool: settings.averages_enabled.
        """
        return self.settings.averages_enabled

    @property
    def averages_count(self):
        """Sets the number of measurements to combine for an average. Must also set SENS:AVER[:STATe] ON

        Returns:
            int: settings.averages_count.
        """
        return self.settings.averages_count

    @property
    def averages_mode(self):
        """Sets the type of averaging to perform: Point or Sweep (default is sweep).

        Returns:
            Enum: settings.averages_mode.
        """
        return self.settings.averages_mode

    @log_set_parameter
    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: int = 1, port: int = 1) -> None:
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int): Channel identifier of the parameter to update.
            port (int): Port identifier of the parameter to update.
        """
    #     def set_parameter(self, parameter: Parameter, value: ParameterValue):
    # """Set various parameters for the VNA."""
    
        if parameter == Parameter.POWER:
            self.settings.source_power = float(value)
            if self.is_device_active():
                self.device.source_power(self.settings.source_power)
            return
        
        if parameter == Parameter.FREQUENCY_START:
            self.settings.start_freq = float(value)
            if self.is_device_active():
                self.device.start_freq(self.settings.start_freq)
            return

        if parameter == Parameter.POWER:
            self.settings.power = float(value)
            if self.is_device_active():
                self.device.power(self.power)
            return


        if parameter == Parameter.FREQUENCY_STOP:
            self.settings.stop_freq = float(value)
            if self.is_device_active():
                self.device.stop_freq(self.settings.stop_freq)
            return
        
        if parameter == Parameter.FREQUENCY_CENTER:
            self.settings.center_freq = float(value)
            if self.is_device_active():
                self.device.center_freq(self.settings.center_freq)
            return
        
        if parameter == Parameter.STEP_AUTO:
            self.settings.step_auto = bool(value)
            if self.is_device_active():
                self.device.step_auto(self.settings.step_auto)
            return
        
        if parameter == Parameter.STEP_SIZE:
            self.settings.step_size = float(value)
            if self.is_device_active():
                self.device.step_size(self.settings.step_size)
            return
        
        if parameter == Parameter.SPAN:
            self.settings.span = float(value)
            if self.is_device_active():
                self.device.span(self.settings.span)
            return
        
        if parameter == Parameter.CW_FREQUENCY:
            self.settings.cw = float(value)
            if self.is_device_active():
                self.device.cw(self.settings.cw)
            return
        
        if parameter == Parameter.NUMBER_POINTS:
            self.settings.points = int(value)
            if self.is_device_active():
                self.device.points(self.settings.points)
            return
        
        if parameter == Parameter.IF_BANDWIDTH:
            self.settings.if_bandwidth = float(value)
            if self.is_device_active():
                self.device.if_bandwidth(self.settings.if_bandwidth)
            return
        
        if parameter == Parameter.SWEEP_MODE:
            self.settings.sweep_type = value  # Assuming Enum type
            if self.is_device_active():
                self.device.sweep_type(self.settings.sweep_type)
            return
        
        if parameter == Parameter.AVERAGING_ENABLED:
            self.settings.averages_enabled = bool(value)
            if self.is_device_active():
                self.device.averages_enabled(self.settings.averages_enabled)
            return
        
        if parameter == Parameter.NUMBER_AVERAGES:
            self.settings.averages_count = int(value)
            if self.is_device_active():
                self.device.averages_count(self.settings.averages_count)
            return
        
        if parameter == Parameter.AVERAGES_MODE:
            self.settings.averages_mode = value  # Assuming Enum type
            if self.is_device_active():
                self.device.averages_mode(self.settings.averages_mode)
            return
        
        raise ParameterNotFound(self, parameter)



    def get_parameter(self, parameter: Parameter):
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
        """
        if parameter == Parameter.POWER:
            return self.settings.power
        if parameter == Parameter.IF_BANDWIDTH:
            return self.settings.if_bandwidth
        if parameter == Parameter.SWEEP_MODE:
            return self._get_sweep_mode()
        if parameter == Parameter.DEVICE_TIMEOUT:
            return self.device_timeout
        raise ParameterNotFound(self, parameter)

    def _set_parameter_str(self, parameter: Parameter, value: str):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (str): new value
        """
        if parameter == Parameter.SWEEP_MODE:
            self.set_sweep_mode(VNASweepModes(value))
            return

        super()._set_parameter_str(parameter, value)

    def set_power(self, power: float, channel=1, port=1):
        """sets the power in dBm"""
        self.settings.power = power
        if self.is_device_active():
            self.send_command(f"SOUR{channel}:POW{port}", f"{self.settings.power:.1f}")

    def set_if_bandwidth(self, value: float, channel=1):
        """sets the if bandwidth in Hz"""
        self.settings.if_bandwidth = value
        if self.is_device_active():
            bandwidth = str(self.settings.if_bandwidth)
            self.send_command(f"SENS{channel}:BWID", bandwidth)

    def get_sweep_mode(self):
        """VectorNetworkAnalyzer'sweep_mode' property.

        Returns:mode
            str: settings.sweep_mode.
        """
        return self.settings.sweep_mode

    def set_sweep_mode(self, value: str, channel=1):
        """
        Sets the sweep mode

        Input:
            mode (str) : Sweep mode: 'hold', 'cont', single' and 'group'
        """
        self.settings.sweep_mode = VNASweepModes(value)
        if self.is_device_active():
            mode = self.settings.sweep_mode.name
            self.send_command(f"SENS{channel}:SWE:MODE", mode)

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

    def _get_sweep_mode(self, channel=1):
        """Return the current sweep mode."""
        return str(self.send_query(f":SENS{channel}:SWE:MODE?")).rstrip()

    def _get_trace(self, channel=1, trace=1):
        """Get the data of the current trace."""
        self.send_command(command="FORM:DATA", arg="REAL,32")
        self.send_command(command="FORM:BORD", arg="SWAPPED")  # SWAPPED
        data = self.send_binary_query(f"CALC{channel}:MEAS{trace}:DATA:SDAT?")
        datareal = np.array(data[::2])  # Elements from data starting from 0 iterating by 2
        dataimag = np.array(data[1::2])  # Elements from data starting from 1 iterating by 2

        return datareal + 1j * dataimag

    def _set_count(self, count: str, channel=1):
        """
        Sets the trigger count (groups)
        Input:
            count (str) : Count number
        """
        self.send_command(f"SENS{channel}:SWE:GRO:COUN", count)

    def _pre_measurement(self):
        """
        Set everything needed for the measurement
        Averaging has to be enabled.
        Trigger count is set to number of averages
        """
        if not self.averaging_enabled:
            self.averaging_enabled = True
            self.number_averages = 1
        self._set_count(str(self.settings.number_averages))

    def _start_measurement(self, channel=1):
        """
        This function is called at the beginning of each single measurement in the spectroscopy script.
        Also, the averages need to be reset.
        """
        self.average_clear()
        self.settings.sweep_mode = VNASweepModes("group")
        mode = self.settings.sweep_mode.name
        self.send_command(f"SENS{channel}:SWE:MODE", mode)

    def _wait_until_ready(self, period=0.25) -> bool:
        """Waiting function to wait until VNA is ready."""
        timelimit = time.time() + self.device_timeout
        while time.time() < timelimit:
            if self.ready():
                return True
            time.sleep(period)
        return False

    def average_clear(self, channel=1):
        """Clears the average buffer."""
        self.send_command(command=f":SENS{channel}:AVER:CLE", arg="")

    def get_frequencies(self):
        """return freqpoints"""
        return np.array(self.send_binary_query("SENS:X?"))

    def ready(self) -> bool:
        """
        This is a proxy function.
        Returns True if the VNA is on HOLD after finishing the required number of averages.
        """
        try:  # the VNA sometimes throws an error here, we just ignore it
            return self._get_sweep_mode() == "HOLD"
        except Exception:  # noqa: BLE001
            return False

    def release(self, channel=1):
        """Bring the VNA back to a mode where it can be easily used by the operator."""
        self.settings.sweep_mode = VNASweepModes("cont")
        mode = self.settings.sweep_mode.name
        self.send_command(f"SENS{channel}:SWE:MODE", mode)

    def read_tracedata(self):
        """
        Return the current trace data.
        It already releases the VNA after finishing the required number of averages.
        """
        self._pre_measurement()
        self._start_measurement()
        if self._wait_until_ready():
            trace = self._get_trace()
            self.release()
            return trace
        raise TimeoutError("Timeout waiting for trace data")

    def acquire_result(self):
        """Convert the data received from the device to a Result object."""
        return VNAResult(data=self.read_tracedata())
