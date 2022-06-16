"""StepAttenuator class."""
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import urlopen

from qililab.config import logger
from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import Device, InstrumentName


@InstrumentFactory.register
class StepAttenuator(Instrument):
    """StepAttenuator class."""

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
        model_name = self.http_request(command="MN?")
        logger.info("Connected to step attenuator with model name %s", model_name)
        self.device = Device()

    def http_request(self, command: str):
        """Send an HTTP request with the given command.

        Args:
            command (str): Command to send via HTTP.
        """
        request = f"http://{self.ip}/:{command}"

        try:
            http_result = urlopen(request, timeout=2)
            pte_return = http_result.read()
        except URLError:
            logger.error("No response from device. Check IP address and connections.")
            pte_return = "No Response!"

        return pte_return

    @property
    def attenuation(self):
        """StepAttenuator 'attenuation' property.

        Returns:
            float: Attenuation.
        """
        return self.settings.attenuation
