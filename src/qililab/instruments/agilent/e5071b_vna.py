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

"""Agilent Vector Network Analyzer E5071B class."""
from dataclasses import dataclass

import numpy as np

from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.result.vna_result import VNAResult
from qililab.typings.enums import InstrumentName
from qililab.typings.instruments.vector_network_analyzer import VectorNetworkAnalyzerDriver


@InstrumentFactory.register
class E5071B(VectorNetworkAnalyzer):
    """Agilent Vector Network Analyzer E5071B"""

    name = InstrumentName.AGILENT_E5071B
    device: VectorNetworkAnalyzerDriver

    @dataclass
    class E5071BSettings(VectorNetworkAnalyzer.VectorNetworkAnalyzerSettings):
        """Contains the settings of a specific VectorNetworkAnalyzer"""

    settings: E5071BSettings

    @VectorNetworkAnalyzer.power.setter  # type: ignore
    def power(self, power: float, channel=1):
        """Set or read current power"""
        self.settings.power = power
        if self.is_device_active():
            self.send_command(command=f":SOUR{channel}:POW:LEV:IMM:AMPL", arg=f"{power}")

    @VectorNetworkAnalyzer.electrical_delay.setter  # type: ignore
    def electrical_delay(self, time: float):
        """Set electrical delay in channel 1

        Input:
            value (str) : Electrical delay in ns
        """
        self.settings.electrical_delay = time
        if self.is_device_active():
            self.send_command("CALC:MEAS:CORR:EDEL:TIME", f"{time}")

    @VectorNetworkAnalyzer.if_bandwidth.setter  # type: ignore
    def if_bandwidth(self, bandwidth: float, channel=1):
        """Set/query IF Bandwidth for specified channel"""
        self.settings.if_bandwidth = bandwidth
        if self.is_device_active():
            self.send_command(command=f":SENS{channel}:BAND:RES", arg=f"{bandwidth}")

    def get_data(self):
        """get data"""
        self.send_command(command=":INIT:CONT", arg="OFF")
        self.send_command(command=":INIT:IMM;", arg="*WAI")
        self.send_command(command="CALC:MEAS:DATA:SDATA?", arg="")
        serialized_data = self.read_raw()
        i_0 = serialized_data.find(b"#")
        number_digits = int(serialized_data[i_0 + 1 : i_0 + 2])
        number_bytes = int(serialized_data[i_0 + 2 : i_0 + 2 + number_digits])
        number_data = number_bytes // 4
        number_points = number_data // 2
        v_data = np.frombuffer(
            serialized_data[(i_0 + 2 + number_digits) : (i_0 + 2 + number_digits + number_bytes)],
            dtype=">f",
            count=number_data,
        )
        # data is in I_0,Q0,I1,Q1,I2,Q2,.. format, convert to complex
        measurementsend_commandplex = v_data.reshape((number_points, 2))
        return measurementsend_commandplex[:, 0] + 1j * measurementsend_commandplex[:, 1]

    def acquire_result(self):
        """Convert the data received from the device to a Result object."""
        return VNAResult(data=self.get_data())

    def continuous(self, continuous: bool):
        """set continuous mode
        Args:
            continuous (bool): continuous flag
        """
        arg = "ON" if continuous else "OFF"
        self.send_command(command=":INIT:CONT", arg=arg)
