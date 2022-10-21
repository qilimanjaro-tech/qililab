"""Vector Network Analyzer generic PyVisa driver"""
from dataclasses import dataclass, field

import numpy as np
import pyvisa

from qililab.constants import DEFAULT_TIMEOUT
from qililab.typings.enums import VNAScatteringParameters
from qililab.typings.instruments.device import Device


@dataclass
class VectorNetworkAnalyzerDriver(Device):
    """Typing class of the Vector Network Analyzer generic PyVisa driver."""

    name: str
    address: str
    timeout: int = DEFAULT_TIMEOUT
    driver: pyvisa.Resource = field(init=False)

    def __post_init__(self):
        resource_manager = pyvisa.ResourceManager("@py")
        self.driver = resource_manager.open_resource(f"TCPIP::{self.address}::INSTR")
        self.driver.timeout = self.timeout

    def initial_setup(self):
        """Set initial preset"""
        self.driver.write("FORM:DATA REAL32")
        self.driver.write("*CLS")
        self.driver.write("SYST:PRES; *OPC?")

    def reset(self):
        """Reset instrument settings."""
        self.driver.write("SYST:PRES; *OPC?")

    def send_command(self, command: str, arg: str = "?"):
        """Function to communicate with the device."""
        return self.driver.write(f"{command} {arg}")  # type: ignore

    def output(self, arg="?"):
        """Turns RF output power on/off
        Give no argument to query current status.
        Parameters
        -----------
        arg : int, str
            Set state to 'ON', 'OFF', 1, 0
        """
        return self.send_command(command=":OUTP", arg=arg)

    def stop(self):
        """close an instrument."""
        self.output(arg="OFF")

    def freq_npoints(self, points="?", channel: str = ""):
        """Set/Query number of points"""
        com_str = f":SENS{channel}:SWE:POIN"
        return int(self.send_command(command=com_str, arg=points))

    def scattering_parameter(self, par: str = "?", trace: int = 1):
        """set scattering parameter"""
        if isinstance(par, str):
            raise ValueError("PAREXC: Par must be a string")
        upper_par = par.upper()
        if upper_par == "?":
            return self.send_command(f"CALC1:PAR{trace}:DEF")
        scatter_param = VNAScatteringParameters(upper_par)
        return self.send_command(f"CALC1:MEAS{scatter_param.value}:PAR", upper_par)

    def autoscale(self):
        """autoscale"""
        self.driver.write("DISP:WIND:TRAC:Y:AUTO")

    def freq_start(self, freq: str = "?", channel: str = ""):
        """Set/query start frequency"""
        com_str = f":SENS{channel}:FREQ:STAR"
        return float(self.send_command(command=com_str, arg=freq))

    def freq_stop(self, freq: str = "?", channel: str = ""):
        """Set/query stop frequency"""
        com_str = f":SENS{channel}:FREQ:STOP"
        return float(self.send_command(command=com_str, arg=freq))

    def freq_center(self, freq: str = "?", channel: str = ""):
        """Set/query center frequency in Hz"""
        com_str = f":SENS{channel}:FREQ:CENT"
        return float(self.send_command(command=com_str, arg=freq))

    def freq_span(self, freq: str = "?", channel: str = ""):
        """Set/query span in Hz"""
        com_str = f":SENS{channel}:FREQ:SPAN"
        return float(self.send_command(command=com_str, arg=freq))

    def power(self, power: str = "?", channel: str = ""):
        """Set or read current power"""
        com_str = f":SOUR{channel}:POW:LEV:IMM:AMPL"
        return float(self.send_command(command=com_str, arg=power))

    def if_bandwidth(self, bandwidth: str = "?", channel: str = ""):
        """Set/query IF Bandwidth for specified channel"""
        com_str = f":SENS{channel}:BAND:RES"
        return self.send_command(command=com_str, arg=bandwidth)

    def electrical_delay(self, time: str):
        """Set electrical delay in 1
        example input: time = '100E-9' for 100ns"""
        self.driver.write(f"CALC:MEAS:CORR:EDEL:TIME {time}")  # type: ignore

    def get_data(self):  # sourcery skip: simplify-division
        """get data"""
        self.driver.write("CALC:MEAS:DATA:Serialized_dATA?")
        serialized_data = self.driver.read_raw()
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

    def read(self) -> str:
        """read the channel data"""
        return self.driver.read()  # type: ignore

    def average_state(self, state="?", channel=""):
        """Sets/query averaging state"""
        com_str = f":SENS{channel}:AVER:STAT"
        return self.send_command(command=com_str, arg=state)

    def average_count(self, count="?", channel=""):
        """Set/query number of averages"""
        com_str = f":SENS{channel}:AVER:COUN"
        return int(self.send_command(command=com_str, arg=count))
