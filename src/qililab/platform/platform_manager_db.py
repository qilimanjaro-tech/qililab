"""PlatformManagerDB class."""
from qililab.config import logger
from qililab.platform.platform import Platform
from qililab.platform.platform_manager import PlatformManager
from qililab.remote_connection import RemoteAPI
from qililab.settings import RuncardSchema


class PlatformManagerDB(PlatformManager):
    """Manager of platform objects."""

    def build(self, platform_name: str, remote_api: RemoteAPI | None = None) -> Platform:
        """Build platform.

        Args:
            platform_name (str): Name of the platform to load.
            remote_api (RemoteAPI, optional): Object with which making the web calls

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform")
        platform_settings = self._load_platform_settings(platform_name=platform_name, remote_api=remote_api)
        platform_schema = RuncardSchema(**platform_settings)
        return Platform(runcard_schema=platform_schema)

    def _load_platform_settings(self, platform_name: str, remote_api: RemoteAPI | None = None) -> dict:
        """Load platform and schema settings.

        Args:
            platform_name (str): Name of the platform to request to the database
            remote_api (RemoteAPI, optional): Object with which making the web calls

        Returns:
            dict: Dictionary with platform and schema settings.
        """

        if remote_api is None:
            raise ValueError("Cannot get RUNCARD from database without a defined connection")
        return remote_api.connection.get_runcard(runcard_name=platform_name).runcard
