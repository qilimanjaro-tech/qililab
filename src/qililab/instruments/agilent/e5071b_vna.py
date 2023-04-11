"""Agilent Vector Network Analyzer E5071B class."""
from dataclasses import dataclass

import numpy as np

from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.result.vna_result import VNAResult
from qililab.typings.enums import InstrumentName
from qililab.typings.instruments.agilent_e5071b import E5071BDriver


@InstrumentFactory.register
class E5071B(VectorNetworkAnalyzer):
    """Agilent Vector Network Analyzer E5071B"""

    name = InstrumentName.AGILENT_E5071B
    device: E5071BDriver

    @dataclass
    class E5071BSettings(VectorNetworkAnalyzer.VectorNetworkAnalyzerSettings):
        """Contains the settings of a specific VectorNetworkAnalyzer"""

    settings: E5071BSettings

    @VectorNetworkAnalyzer.power.setter  # type: ignore
    def power(self, power: str = "?", channel: str = ""):
        """Set or read current power"""
        com_str = f":SOUR{channel}:POW:LEV:IMM:AMPL"
        return float(self.send_command(command=com_str, arg=power))

    @VectorNetworkAnalyzer.electrical_delay.setter  # type: ignore
    def electrical_delay(self, time: str):
        """Set electrical delay in 1
        example input: time = '100E-9' for 100ns"""
        self.send_command("CALC:MEAS:CORR:EDEL:TIME", time)  # type: ignore

    @VectorNetworkAnalyzer.if_bandwidth.setter  # type: ignore
    def if_bandwidth(self, bandwidth: str = "?", channel: str = ""):
        """Set/query IF Bandwidth for specified channel"""
        com_str = f":SENS{channel}:BAND:RES"
        return self.send_command(command=com_str, arg=bandwidth)

    def initial_setup(self):
        """Set initial instrument settings."""

    def get_data(self):  # sourcery skip: simplify-division
        """get data"""
        self.send_command(":INIT:CONT OFF")
        self.send_command(":INIT:IMM; *WAI")
        self.send_command("CALC:MEAS:DATA:SDATA?")
        serialized_data = self.device.driver.read_raw()
        i_0 = serialized_data.find(b"#")
        number_digits = int(serialized_data[i_0 + 1 : i_0 + 2])
        number_bytes = int(serialized_data[i_0 + 2 : i_0 + 2 + number_digits])
        number_data = int(number_bytes / 4)
        number_points = int(number_data / 2)
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

    def read(self) -> str:
        """read directly from the device"""
        return self.device.read()

    def send_command(self, command: str, arg: str = "?"):
        """Function to communicate with the device."""
        return self.device.send_command(f"{command} {arg}")  # type: ignore

    def continuous(self, continuous: bool):
        """set continuous mode
        Args:
            continuous (bool): continuous flag
        """
        command = ":INIT:CONT " + ("ON" if continuous else "OFF")
        self.send_command(command=command, arg="")

    def set_timeout(self, value: float):
        """set timeout in mili seconds"""
        self.device.set_timeout(value)
