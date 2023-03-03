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
        """configure driver and connect to the resource"""
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

    def npoints(self, npoints):
        self.driver.write(":SENS1:SWE:POIN %i" % (npoints))

    def power(self, power, port=1):
        self.driver.write("SOUR%i:POW%i %.1f" % (1, port, power))

    def freq_center(self, cf):
        self.driver.write("SENS%i:FREQ:CENT %f" % (1, cf))

    def freq_span(self, span):
        self.driver.write("SENS%i:FREQ:SPAN %i" % (1, span))

    def freq_start(self, val):
        self.driver.write("SENS%i:FREQ:STAR %f" % (1, val))

    def freq_stop(self, val):
        self.driver.write("SENS%i:FREQ:STOP %f" % (1, val))

    def if_bandwidth(self, band):
        self.driver.write("SENS%i:BWID %i" % (1, band))

    def get_freqs(self):
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
        data = self.driver.query_binary_values("CALC%i:MEAS%i:DATA:SDAT?" % (1, 1))
        data_size = np.size(data)
        datareal = np.array(data[0:data_size:2])
        dataimag = np.array(data[1:data_size:2])

        return datareal + 1j * dataimag

    def set_sweep_mode(self, mode, channel=1):
        """
        select the sweep mode from 'hold', 'cont', single' and "group"
        single means only one single trace, not all the averages even if averages
            larger than 1 and Average==True
        """
        mode = mode.lower()
        if mode == "hold":
            self.driver.write("SENS%i:SWE:MODE HOLD" % channel)
        elif mode == "cont":
            self.driver.write("SENS%i:SWE:MODE CONT" % channel)
        elif mode == "single":
            self.driver.write("SENS%i:SWE:MODE SING" % channel)
        elif mode == "group":
            self.driver.write("SENS%i:SWE:MODE GRO" % channel)
        else:
            print("invalid mode")

    def ready(self):
        """
        This is a proxy function, returning True when the VNA is on HOLD after finishing the required number of averages .
        """
        try:  # the VNA sometimes throws an error here, we just ignore it
            return self.get_sweep_mode() == "HOLD"
        except Exception:
            return False

    def get_sweep_mode(self, channel=1):
        return str(self.driver.query(":SENS%i:SWE:MODE?" % channel)).rstrip()

    def release(self):
        self.set_sweep_mode("cont")

    def get_trace(self):
        self.set_sweep_mode("group")
        while not self.ready():
            pass
        return self.get_tracedata()
