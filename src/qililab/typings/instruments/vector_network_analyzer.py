"""Vector Network Analyzer generic PyVisa driver"""
import time
from dataclasses import dataclass, field

import numpy as np
import pyvisa

from qililab.constants import DEFAULT_TIMEOUT
from qililab.typings.enums import VNAScatteringParameters, VNASweepModes
from qililab.typings.instruments.device import Device


@dataclass
class VectorNetworkAnalyzerDriver(Device):
    """Typing class of the Vector Network Analyzer generic PyVisa driver."""

    name: str
    address: str
    avg_state: bool = False
    avg_count: str = "1"
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
        return self.driver.write(f"{command} {arg}")  # type: ignore

    def autoscale(self):
        """autoscale"""
        self.driver.write("DISP:WIND:TRAC:Y:AUTO")

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
        """Close an instrument."""
        self.output(arg="OFF")

    def electrical_delay(self, etime: str):  # MP 04/2017
        """
        Set electrical delay in channel 1

        Input:
            etime (str) : Electrical delay in ns
                example: etime = '100E-9' for 100ns
        """
        self.send_command("SENS1:CORR:EXT:PORT1:TIME", etime)

    def average_clear(self, channel=1):
        """Clears the average buffer."""
        self.send_command(command=f":SENS{channel}:AVER:CLE", arg="")

    def average_count(self, count: str, channel=1):
        """
        Set number of averages
        Input:
            count (str) : Number of averages
        """
        self.avg_count = count
        self.send_command(f"SENS{channel}:AVER:COUN", count)
        self.send_command(command=f":SENS{channel}:AVER:CLE", arg="")

    def freq_npoints(self, points: str):
        """
        Set Number of Points for sweep

        Input:
            points (str) : Number of Points
        """
        self.send_command(":SENS1:SWE:POIN", points)

    def power(self, power: str, channel=1, port=1):
        """
        Set probe power

        Input:
            power (str) : Power in dBm
        """
        self.send_command(f"SOUR{channel}:POW{port}", power)

    def freq_center(self, freq: str, channel=1):
        """
        Set the center frequency

        Input:
            freq (str) : Center Frequency in Hz
        """
        self.send_command(f"SENS{channel}:FREQ:CENT", freq)

    def freq_span(self, freq: str, channel=1):
        """
        Set Span

        Input:
            freq (str) : Span in KHz
        """
        self.send_command(f"SENS{channel}:FREQ:SPAN", freq)

    def freq_start(self, freq: str, channel=1):
        """
        Set Start frequency

        Input:
            freq (str) : Frequency in Hz
        """
        self.send_command(f"SENS{channel}:FREQ:STAR", freq)

    def freq_stop(self, freq: str, channel=1):
        """
        Set Stop frequency

        Input:
            freq (str) : Stop Frequency in Hz
        """
        self.send_command(f"SENS{channel}:FREQ:STOP", freq)

    def if_bandwidth(self, bandwidth: str, channel=1):
        """
        Set Bandwidth

        Input:
            bandwidth (str) : Bandwidth in Hz
        """
        self.send_command(f"SENS{channel}:BWID", bandwidth)

    def get_freqs(self):
        """Return freqpoints"""
        return np.array(self.driver.query_binary_values("SENS:X?"))

    def scattering_parameter(self, par: str = "?", trace: int = 1):
        """Set scattering parameter."""
        if not isinstance(par, str):
            raise ValueError("PAREXC: Par must be a string")
        upper_par = par.upper()
        if upper_par == "?":
            return self.send_command(f"CALC1:PAR{trace}:DEF")
        scatter_param = VNAScatteringParameters(upper_par)
        return self.send_command(f"CALC1:MEAS{trace}:PAR", scatter_param.value)

    def set_timeout(self, value: float):
        """Set timeout in mili seconds."""
        self.timeout = value
        self.driver.timeout = self.timeout

    def get_trace(self, channel=1, trace=1):
        """Get the data of the current trace."""
        self.driver.write("FORM:DATA REAL,32")
        self.driver.write("FORM:BORD SWAPPED")  # SWAPPED
        data = self.driver.query_binary_values(f"CALC{channel}:MEAS{trace}:DATA:SDAT?")
        datareal = np.array(data[::2])  # Elements from data starting from 0 iterating by 2
        dataimag = np.array(data[1::2])  # Elements from data starting from 1 iterating by 2

        return datareal + 1j * dataimag

    def set_sweep_mode(self, mode: str, channel=1):
        """
        Set the sweep mode

        Input:
            mode (str) : Sweep mode: 'hold', 'cont', single' and 'group'
        """
        if not isinstance(mode, str):
            raise ValueError("MODEEXC: Mode must be a string")
        lower_mode = mode.lower()
        sweep_mode = VNASweepModes(lower_mode)
        self.send_command(f"SENS{channel}:SWE:MODE", sweep_mode.name)

    def get_sweep_mode(self, channel=1):
        """Return the current sweep mode."""
        return str(self.driver.query(f":SENS{channel}:SWE:MODE?")).rstrip()

    def ready(self) -> bool:
        """
        This is a proxy function.
        Returns True if the VNA is on HOLD after finishing the required number of averages.
        """
        try:  # the VNA sometimes throws an error here, we just ignore it
            return self.get_sweep_mode() == "HOLD"
        except Exception:
            return False

    def release(self):
        """Bring the VNA back to a mode where it can be easily used by the operator."""
        self.set_sweep_mode("cont")

    def average_state(self, state: bool, channel=1):
        """Set status of Average."""
        if state:
            self.avg_state = True
            self.send_command(f"SENS{channel}:AVER:STAT", "ON")
        else:
            self.avg_state = False
            self.send_command(f"SENS{channel}:AVER:STAT", "OFF")

    def set_count(self, count: str, channel=1):
        """
        Sets the trigger count (groups)
        Input:
            count (str) : Count number
        """
        self.send_command(f"SENS{channel}:SWE:GRO:COUN", count)

    def pre_measurement(self):
        """
        Set everything needed for the measurement
        Averaging has to be enabled.
        Trigger count is set to number of averages
        """
        if not self.avg_state:
            self.average_state(state="True")
            self.average_count(count="1")
        self.set_count(self.avg_count)

    def start_measurement(self):
        """
        This function is called at the beginning of each single measurement in the spectroscopy script.
        Also, the averages need to be reset.
        """
        self.average_clear()
        self.set_sweep_mode("group")

    def wait_until_ready(self, period=0.25) -> bool:
        """Waiting function to wait until VNA is ready."""
        timelimit = time.time() + self.timeout
        while time.time() < timelimit:
            if self.ready():
                return True
            time.sleep(period)
        return False

    def read_tracedata(self):
        """
        Returnthe current trace data.
        It already releases the VNA after finishing the required number of averages.
        """
        self.pre_measurement()
        self.start_measurement()
        if self.wait_until_ready():
            trace = self.get_trace()
            self.release()
            return trace
        raise TimeoutError("Timeout waiting for trace data")
