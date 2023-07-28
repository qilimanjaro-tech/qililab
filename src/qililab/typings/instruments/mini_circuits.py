"""MiniCircuits driver."""

import urllib
from dataclasses import dataclass

from qililab.typings.instruments.device import Device


@dataclass
class MiniCircuitsDriver(Device):
    """Typing class of the driver for the MiniCircuits instrument.

    Args:
        name (str): Name of the instrument
        address (str): IP address of the instrument
    """

    name: str
    address: str

    def __post_init__(self):
        """Initialize the driver."""
        self._http_request(command="MN?")

    def setup(self, attenuation: float):
        """Set instrument settings."""
        self._http_request(command=f"SETATT={attenuation}")

    def get(self):
        return float(self._http_request("ATT?"))

    def _http_request(self, command: str):
        """Send an HTTP request with the given command.

        Args:
            command (str): Command to send via HTTP.
        """
        try:
            request = urllib.request.Request(f"http://{self.address}/:{command}")  # type: ignore
            with urllib.request.urlopen(request, timeout=2) as response:  # type: ignore # nosec
                pte_return = response.read()
        except urllib.error.URLError as error:  # type: ignore
            raise ValueError("No response from device. Check IP address and connections.") from error

        return pte_return
