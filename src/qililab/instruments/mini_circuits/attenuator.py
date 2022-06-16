"""Attenuator class."""
import urllib
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import Device, InstrumentName


@InstrumentFactory.register
class Attenuator(Instrument):
    """Attenuator class."""

    name = InstrumentName.MINI_CIRCUITS

    @dataclass
    class StepAttenuatorSettings(Instrument.InstrumentSettings):
        """Step attenuator settings."""

        attenuation: float

    settings: StepAttenuatorSettings

    def start(self):
        """Start instrument."""

    def stop(self):
        """Stop instrument."""

    def setup(self):
        """Set instrument settings."""
        self.http_request(command=f"SETATT={self.attenuation}")

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.http_request(command="MN?")
        self.device = Device()

    def http_request(self, command: str):
        """Send an HTTP request with the given command.

        Args:
            command (str): Command to send via HTTP.
        """
        try:
            request = urllib.request.Request(f"http://{self.ip}/:{command}")  # type: ignore
            with urllib.request.urlopen(request, timeout=2) as response:  # type: ignore # nosec
                pte_return = response.read()
        except urllib.error.URLError as error:  # type: ignore
            raise ValueError("No response from device. Check IP address and connections.") from error

        return pte_return

    @property
    def attenuation(self):
        """Attenuator 'attenuation' property.

        Returns:
            float: Attenuation.
        """
        return self.settings.attenuation
