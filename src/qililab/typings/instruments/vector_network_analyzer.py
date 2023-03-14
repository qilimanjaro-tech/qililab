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
    timeout: float = DEFAULT_TIMEOUT
    driver: pyvisa.Resource = field(init=False)

    def __post_init__(self):
        """Configure driver and connect to the resource"""
        resource_manager = pyvisa.ResourceManager("@py")
        self.driver = resource_manager.open_resource(f"TCPIP::{self.address}::INSTR")
        self.driver.timeout = self.timeout

    def initial_setup(self):
        """Set initial preset"""
        self.driver.write("FORM:DATA REAL,32")
        self.driver.write("*CLS")
        # this resets the device!
        self.driver.write("SYST:PRES; *OPC?")

    def reset(self):
        """Reset instrument settings."""
        self.driver.write("SYST:PRES; *OPC?")

    def send_command(self, command: str, arg: str = "?"):
        """Function to communicate with the device."""
        return self.driver.write(f"{command} {arg} *WAI")  # type: ignore

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

    def average_count(self, count, channel=1):
        """
        Set number of averages
        Input:
            count (int) : Number of averages
        """
        self.driver.write(f"SENS{channel}:AVER:COUN {count}")
        self.driver.write(f":SENS{channel}:AVER:CLE")

    def freq_npoints(self, points):
        """
        Set Number of Points for sweep

        Input:
            npoints (int)
                Number of Points
        """
        self.driver.write(f":SENS1:SWE:POIN {points}")

    def power(self, power, channel=1, port=1):
        """
        Set probe power

        Input:
            power (float) : Power in dBm
        """
        self.driver.write(f"SOUR{channel}:POW{port} {power:.1f}")

    def freq_center(self, freq, channel=1):
        """
        Set the center frequency

        Input:
            cf (float) : Center Frequency in Hz
        """
        self.driver.write(f"SENS{channel}:FREQ:CENT {freq}")

    def freq_span(self, freq, channel=1):
        """
        Set Span

        Input:
            span (float) : Span in KHz
        """
        self.driver.write(f"SENS{channel}:FREQ:SPAN {freq}")

    def freq_start(self, freq, channel=1):
        """
        Set Start frequency

        Input:
            val (float) : Frequency in Hz
        """
        self.driver.write(f"SENS{channel}:FREQ:STAR {freq}")

    def freq_stop(self, freq, channel=1):
        """
        Set Stop frequency

        Input:
            val (float) : Stop Frequency in Hz
        """
        self.driver.write(f"SENS{channel}:FREQ:STOP {freq}")

    def if_bandwidth(self, bandwidth, channel=1):
        """
        Set Bandwidth

        Input:
            band (float) : Bandwidth in Hz
        """
        self.driver.write(f"SENS{channel}:BWID {bandwidth}")

    def get_freqs(self):
        """Retrun freqpoints"""
        return np.array(self.driver.query_binary_values("SENS:X?"))

    def scattering_parameter(self, par: str = "?", trace: int = 1):
        """set scattering parameter"""
        if not isinstance(par, str):
            raise ValueError("PAREXC: Par must be a string")
        upper_par = par.upper()
        if upper_par == "?":
            return self.send_command(f"CALC1:PAR{trace}:DEF")
        scatter_param = VNAScatteringParameters(upper_par)
        return self.send_command(f"CALC1:MEAS{trace}:PAR", scatter_param.value)

    def autoscale(self):
        """autoscale"""
        self.driver.write("DISP:WIND:TRAC:Y:AUTO")

    def set_timeout(self, value: float):
        """set timeout in mili seconds"""
        self.timeout = value
        self.driver.timeout = self.timeout

    def get_tracedata(self, channel=1, trace=1):
        """
        Get the data of the current trace
        """
        self.driver.write("FORM:DATA REAL,32")
        self.driver.write("FORM:BORD SWAPPED")  # SWAPPED
        data = self.driver.query_binary_values(f"CALC{channel}:MEAS{trace}:DATA:SDAT?")
        data_size = np.size(data)
        datareal = np.array(data[0:data_size:2])
        dataimag = np.array(data[1:data_size:2])

        return datareal + 1j * dataimag

    def set_sweep_mode(self, mode, channel=1):
        """
        Select the sweep mode from 'hold', 'cont', single' and "group"
        single means only one single trace, not all the averages even if averages
            larger than 1 and Average==True
        """
        mode = mode.lower()
        if mode == "hold":
            self.driver.write(f"SENS{channel}:SWE:MODE HOLD")
        elif mode == "cont":
            self.driver.write(f"SENS{channel}:SWE:MODE CONT")
        elif mode == "single":
            self.driver.write(f"SENS{channel}:SWE:MODE SING")
        elif mode == "group":
            self.driver.write(f"SENS{channel}:SWE:MODE GRO")
        else:
            print("invalid mode")

    def ready(self):
        """
        This is a proxy function.
        Returns True if the VNA is on HOLD after finishing the required number of averages.
        """
        try:  # the VNA sometimes throws an error here, we just ignore it
            return self.get_sweep_mode() == "HOLD"
        except Exception:
            return False

    def get_sweep_mode(self, channel=1):
        """
        Return the current sweep mode
        """
        return str(self.driver.query(f":SENS{channel}:SWE:MODE?")).rstrip()

    def release(self):
        """
        Bring the VNA back to a mode where it can be easily used by the operator.
        """
        self.set_sweep_mode("cont")

    def electrical_delay(self, time):  # MP 04/2017
        """
        Set electrical delay in channel 1
        example input: time = '100E-9' for 100ns
        """
        self.driver.write(f"SENS1:CORR:EXT:PORT1:TIME {time:.12f}")

    def average_state(self, state, channel=1):
        """
        Set status of Average
        """
        if state in ["True", "1"]:
            self.driver.write(f"SENS{channel}:AVER:STAT ON")
        elif state in ["False", "0"]:
            self.driver.write(f"SENS{channel}:AVER:STAT OFF")
        else:
            raise ValueError("average state can only set True or False")

    def get_trace(self):
        """
        Return trace data
        """
        self.set_sweep_mode("group")
        while not self.ready():
            pass
        return self.get_tracedata()

    def read(self):
        """read directly from the device"""
        raise NotImplementedError
