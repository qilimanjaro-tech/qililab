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
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.result.vna_result import VNAResult
from qililab.typings.enums import InstrumentName, Parameter, VNASweepModes
from qililab.typings.instruments.vector_network_analyzer import VectorNetworkAnalyzerDriver


@InstrumentFactory.register
class E5080B(VectorNetworkAnalyzer):

    """KeySight Vector Network Analyzer E5080B"""

    name = InstrumentName.KEYSIGHT_E5080B
    device: VectorNetworkAnalyzerDriver

    @dataclass
    class E5080BSettings(VectorNetworkAnalyzer.VectorNetworkAnalyzerSettings):
        """Contains the settings of a specific VectorNetworkAnalyzer.

        Args:
            sweep_mode (str): Sweeping mode of the instrument
        """

        sweep_mode: VNASweepModes = VNASweepModes.CONT
        device_timeout: float = DEFAULT_TIMEOUT

    settings: E5080BSettings

    def _set_parameter_float(self, parameter: Parameter, value: float):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (float): new value
        """
        if parameter == Parameter.DEVICE_TIMEOUT:
            self.device_timeout = value
            return

        super()._set_parameter_float(parameter, value)

    def _set_parameter_str(self, parameter: Parameter, value: str):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (str): new value
        """
        if parameter == Parameter.SWEEP_MODE:
            self.sweep_mode = VNASweepModes(value)
            return

        super()._set_parameter_str(parameter, value)

    @VectorNetworkAnalyzer.power.setter  # type: ignore
    def power(self, value: float, channel=1, port=1):
        """sets the power in dBm"""
        self.settings.power = value
        if self.is_device_active():
            power = f"{self.settings.power:.1f}"
            self.send_command(f"SOUR{channel}:POW{port}", power)

    @VectorNetworkAnalyzer.if_bandwidth.setter  # type: ignore
    def if_bandwidth(self, value: float, channel=1):
        """sets the if bandwidth in Hz"""
        self.settings.if_bandwidth = value
        if self.is_device_active():
            bandwidth = str(self.settings.if_bandwidth)
            self.send_command(f"SENS{channel}:BWID", bandwidth)

    @VectorNetworkAnalyzer.electrical_delay.setter  # type: ignore
    def electrical_delay(self, value: float):
        """
        Set electrical delay in channel 1

        Input:
            value (str) : Electrical delay in ns
        """
        self.settings.electrical_delay = value
        if self.is_device_active():
            etime = f"{self.settings.electrical_delay:.12f}"
            self.send_command("SENS1:CORR:EXT:PORT1:TIME", etime)

    @property
    def sweep_mode(self):
        """VectorNetworkAnalyzer'sweep_mode' property.

        Returns:mode
            str: settings.sweep_mode.
        """
        return self.settings.sweep_mode

    @sweep_mode.setter
    def sweep_mode(self, value: str, channel=1):
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

    def _start_measurement(self):
        """
        This function is called at the beginning of each single measurement in the spectroscopy script.
        Also, the averages need to be reset.
        """
        self.average_clear()
        self.sweep_mode = "group"

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
        except Exception:  # pylint: disable=broad-except
            return False

    def release(self, channel=1):
        """Bring the VNA back to a mode where it can be easily used by the operator."""
        self.settings.sweep_mode = VNASweepModes("cont")
        self.send_command(f"SENS{channel}:SWE:MODE", self.settings.sweep_mode.value)

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
