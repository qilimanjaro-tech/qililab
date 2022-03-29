from dataclasses import dataclass

from qililab.platforms.abstract_platform import AbstractPlatform
from qililab.settings import SM


@dataclass
class QiliPlatform(AbstractPlatform):
    """Qilimanjaro platform

    Attributes:
        name (str): Name of the platform.
        platform_settings (Settings): Dataclass containing the settings of the platform.
    """

    _ID = "platform"

    def __post_init__(self) -> None:
        """Load platform settings."""
        self.settings = SM.load(name=self.name, id=self._ID)
