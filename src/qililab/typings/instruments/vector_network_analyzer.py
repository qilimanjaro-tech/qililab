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
        self.driver.timeout = self.timeout

    def initial_setup(self):
        """Set initial preset"""
        self.driver.write("FORM:DATA REAL,32")
        self.driver.write("*CLS")
        self.reset()

    def reset(self):
        """Reset instrument settings."""
        self.driver.write("SYST:PRES; *OPC")

    def send_command(self, command: str, arg: str = "?"):
        """Function to communicate with the device."""
        return self.driver.write(f"{command} {arg}")  # type: ignore

    def send_query(self, query: str):
        """Function to communicate with the device."""
        return self.driver.query(query)  # type: ignore

    def send_binary_query(self, query: str):
        """Function to communicate with the device."""
        return self.driver.query_binary_values(query)  # type: ignore

    def set_timeout(self, value: float):
        """Set timeout in mili seconds."""
        self.timeout = value
        self.driver.timeout = self.timeout

    def read(self) -> str:
        """read directly from the device"""
        return self.driver.read()  # type: ignore

    def read_raw(self):
        """read raw data directly from the device"""
        return self.driver.read_raw()  # type: ignore
