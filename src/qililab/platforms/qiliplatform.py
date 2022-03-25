from qililab.config import raise_error
from qililab.platforms.abstract_platform import AbstractPlatform
from qililab.settings.settings_manager import SettingsManager


class QiliPlatform(AbstractPlatform):
    """Qilimanjaro platform

    Attributes:
        name (str): Name of the platform.
        platform_settings (Settings): Dataclass containing the settings of the platform.

    """

    _ID = "platform"

    def __init__(self, name: str) -> None:
        super().__init__(name=name)
        self.platform_settings = SettingsManager(name=self.name, id=self._ID)

    def connect(self) -> None:
        """Connect to lab instruments using the specified calibration settings."""
        raise_error(NotImplementedError)

    def setup(self) -> None:
        """Configure instruments using the specified calibration settings."""
        raise_error(NotImplementedError)

    def start(self) -> None:
        """Turn on lab instruments."""
        raise_error(NotImplementedError)

    def stop(self) -> None:
        """Turn off lab instruments."""
        raise_error(NotImplementedError)

    def disconnect(self) -> None:
        """Disconnect from lab instruments."""
        raise_error(NotImplementedError)

    # TODO: Replace 'object' with PulseSequence class (when defined)
    def execute(self, sequence: object, nshots: int = None):
        """Execute a pulse sequence.

        Args:
            sequence (PulseSequence): Pulse sequence to execute.
            nshots (int): Number of shots to sample from the experiment. If ``None`` the default
            value provided as hardware_avg in the calibration json will be used.

        Returns:
            Readout results.
        """
        raise_error(NotImplementedError)
