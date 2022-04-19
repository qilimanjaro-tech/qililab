from qililab.settings import PlatformSettings


class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        name (str): Name of the platform.
        settings (Settings): Dataclass containing the settings of the platform.
    """

    def __init__(self, name: str, settings: dict):
        self.name = name
        self.settings = PlatformSettings(**settings)

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return self.name
