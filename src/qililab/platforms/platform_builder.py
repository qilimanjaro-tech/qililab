from dataclasses import dataclass
from typing import ClassVar

from qililab.platforms.abstract_platform import AbstractPlatform
from qililab.settings import SM


@dataclass
class PlatformBuilder(AbstractPlatform):
    """Qilimanjaro platform

    Attributes:
        name (str): Name of the platform.
        platform_settings (Settings): Dataclass containing the settings of the platform.
    """

    _id: ClassVar[str] = "platform"

    def __post_init__(self) -> None:
        """Load platform settings."""
        super().__post_init__()
        # TODO: Add "lab" (global?) variable instead of "qili"
        self.settings = SM.load(filename=self.name, category=self._id)
