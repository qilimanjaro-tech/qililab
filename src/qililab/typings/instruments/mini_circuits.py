# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
