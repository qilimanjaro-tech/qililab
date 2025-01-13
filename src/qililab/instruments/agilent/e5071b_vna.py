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

from qililab.instruments.decorators import log_set_parameter
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.result.vna_result import VNAResult
from qililab.typings import ChannelID, InstrumentName, Parameter, ParameterValue
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

    @log_set_parameter
    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: int = 1, port: int = 1) -> None:
        """Set instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int): Channel identifier of the parameter to update.
            port (int): Port identifier of the parameter to update.
        """
        channel_id = int(channel_id)
        if parameter == Parameter.POWER:
            value = float(value)
            self.set_power(power=value, channel=channel_id)
            return
        if parameter == Parameter.IF_BANDWIDTH:
            value = float(value)
            self.set_if_bandwidth(value=value, channel=channel_id)
            return
        if parameter == Parameter.ELECTRICAL_DELAY:
            self.electrical_delay = value
            return
        raise ParameterNotFound(self, parameter)

    def get_parameter(self, parameter: Parameter, channel_id: ChannelID | None = None):
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None): Channel identifier of the parameter to update.
        """
        if parameter == Parameter.POWER:
            return self.settings.power
        if parameter == Parameter.IF_BANDWIDTH:
            return self.settings.if_bandwidth
        if parameter == Parameter.ELECTRICAL_DELAY:
            return self.settings.electrical_delay
        raise ParameterNotFound(self, parameter)

    def set_power(self, power: float, channel=1, port=1):
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

    def set_if_bandwidth(self, value: float, channel=1):
        """Set/query IF Bandwidth for specified channel"""
        self.settings.if_bandwidth = value
        if self.is_device_active():
            self.send_command(command=f":SENS{channel}:BAND:RES", arg=f"{value}")

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
