"""Vector Network Analyzer generic PyVisa driver"""
from dataclasses import dataclass, field

import pyvisa

from qililab.constants import DEFAULT_TIMEOUT
from qililab.typings.instruments.device import Device


@dataclass
class VectorNetworkAnalyzerDriver(Device):
    """Typing class of the driver for a Vector Network Analyzer instrument."""

    name: str
    address: str
    driver: pyvisa.Resource = field(init=False)
    timeout: float = DEFAULT_TIMEOUT

    def __post_init__(self):
        """Configure driver and connect to the resource"""
        resource_manager = pyvisa.ResourceManager("@py")
        self.driver = resource_manager.open_resource(f"TCPIP::{self.address}::INSTR")

    def initial_setup(self):
        """Set initial preset"""
        self.driver.write("FORM:DATA REAL,32")
        self.driver.write("*CLS")
        # this resets the device!
        self.driver.write("SYST:PRES; *OPC?")

    def reset(self):
        """Reset instrument settings."""
        self.driver.write("SYST:PRES; *OPC?")

    def send_command(self, command: str, arg: str = ""):
        """Function to communicate with the device."""
        return self.driver.write(f"{command} {arg}")  # type: ignore

    def send_query(self, query: str):
        """Function to communicate with the device."""
        return self.driver.query(query)  # type: ignore

    def send_binary_query(self, query: str):
        """Function to communicate with the device."""
        return self.driver.query_binary_values(query)  # type: ignore

    def autoscale(self):
        """Autoscale."""
        self.driver.write("DISP:WIND:TRAC:Y:AUTO")

    def set_timeout(self, value: float):
        """Set timeout in mili seconds."""
        self.timeout = value
