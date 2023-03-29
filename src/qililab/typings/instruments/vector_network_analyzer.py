"""Vector Network Analyzer generic PyVisa driver"""
from dataclasses import dataclass, field

import pyvisa

from qililab.constants import DEFAULT_TIMEOUT
from qililab.typings.instruments.device import Device


@dataclass
class VectorNetworkAnalyzerDriver(Device):
    """Typing class of the Vector Network Analyzer generic PyVisa driver."""

    name: str
    address: str
    driver: pyvisa.Resource = field(init=False)
    timeout: float = DEFAULT_TIMEOUT

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

    def output(self, arg="?"):
        """Turns RF output power on/off
        Give no argument to query current status.
        Parameters
        -----------
        arg : int, str
            Set state to 'ON', 'OFF', 1, 0
        """
        return self.send_command(command=":OUTP", arg=arg)

    def set_timeout(self, value: float):
        """Set timeout in mili seconds."""
        self.timeout = value

    def stop(self):
        """Close an instrument."""
        self.output(arg="OFF")

    def start(self):
        """Open an instrument."""
        self.output(arg="ON")

    def read_tracedata(self):
        """
        Returnthe current trace data.
        It already releases the VNA after finishing the required number of averages.
        """
        pass
