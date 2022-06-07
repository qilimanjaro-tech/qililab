"""StepAttenuator class."""
from urllib.request import urlopen

from qililab.instruments.instrument import Instrument
from qililab.typings import Device
from qililab.config import logger
from qililab.utils import Factory


@Factory.register
class StepAttenuator(Instrument):
    """StepAttenuator class."""

    class StepAttenuatorSettings(Instrument.InstrumentSettings):
        """Step attenuator settings."""

        attenuation: float

    settings: StepAttenuatorSettings

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = self.StepAttenuatorSettings(**settings)

    def start(self):
        """Start instrument."""

    def stop(self):
        """Stop instrument."""

    def setup(self):
        """Set instrument settings."""
        self.HTTP_request(command=f"SETATT={self.attenuation}")

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        model_name = self.HTTP_request(command="MN?")
        logger.info("Connected to step attenuator with model name %s", model_name)
        self.device = Device()

    def HTTP_request(self, command: str):
        """Send an HTTP request with the given command.

        Args:
            command (str): Command to send via HTTP.
        """
        request = "http://" + self.ip + "/:" + command

        try:
            HTTP_Result = urlopen(request, timeout=2)
            PTE_Return = HTTP_Result.read()

        except:
            logger.error("No response from device. Check IP address and connections.")
            PTE_Return = "No Response!"

        return PTE_Return

    @property
    def attenuation(self):
        """StepAttenuator 'attenuation' property.

        Returns:
            float: Attenuation.
        """
        return self.settings.attenuation