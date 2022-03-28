from qililab.platforms.abstract_platform import AbstractPlatform
from qililab.settings import SM


class QiliPlatform(AbstractPlatform):
    """Qilimanjaro platform

    Attributes:
        name (str): Name of the platform.
        platform_settings (Settings): Dataclass containing the settings of the platform.
    """

    _ID = "platform"

    def __init__(self, name: str) -> None:
        """
        Args:
            name (str): Name of the platform
        """
        super().__init__(name=name)
        self.settings = SM.load(name=self.name, id=self._ID)
