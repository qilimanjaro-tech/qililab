"""Class KeySight E5080B"""
from dataclasses import dataclass, field

import pyvisa

from qililab.constants import DEFAULT_TIMEOUT
from qililab.typings.instruments.device import Device


@dataclass
class E5080BDriver(Device):
    """Typing class of the KeySight E5080B PyVisa driver."""

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

    def _com(self, command, arg="?", raw=False):
        """Function to communicate with the device."""
        self.driver.write(f"{command} {arg}")

    def _output(self, arg="?"):
        """Turns RF output power on/off
        Give no argument to query current status.
        Parameters
        -----------
        arg : int, str
            Set state to 'ON', 'OFF', 1, 0
        """
        return self._com(":OUTP", arg)

    def stop(self):
        """close an instrument."""
        self._output(arg="OFF")
