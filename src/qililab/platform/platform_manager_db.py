"""PlatformManagerDB class."""
from qililab import __version__
from qililab.config import logger
from qililab.platform.platform import Platform
from qililab.platform.platform_manager import PlatformManager
from qililab.remote_connection import RemoteAPI
from qililab.settings import RuncardSchema


def _require_remote_api(func):
    """Ensure a remote api instance is passed in the kwargs and that it is not None."""

    def wrapper(*args, **kwargs):
        """Wrapper"""

        if "remote_api" not in kwargs or kwargs["remote_api"] is None:
            raise ValueError("Cannot operate with RUNCARD in database without a provided remote_api")
        func(*args, **kwargs)

    return wrapper


class PlatformManagerDB(PlatformManager):
    """Manager of platform objects."""

    @_require_remote_api
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

    @_require_remote_api
    def dump(self, platform: Platform, remote_api: RemoteAPI | None = None, description: str = ""):
        """Save all platform information into our database.

        Args:
            platform (Platform): Platform to dump.
            remote_api (RemoteAPI, optional): Object with which making the web calls
            description (str): Informative text about the runcard
        """

        remote_api.connection.save_runcard(
            name=platform.name,
            description=description,
            runcard_dict=platform.to_dict(),
            device_id=remote_api.device_id,
            user_id=remote_api.connection.user_id,
            qililab_version=__version__,
        )

    @_require_remote_api
    def _load_platform_settings(self, platform_name: str, remote_api: RemoteAPI | None = None) -> dict:
        """Load platform and schema settings.

        Args:
            platform_name (str): Name of the platform to request to the database
            remote_api (RemoteAPI, optional): Object with which making the web calls

        Returns:
            dict: Dictionary with platform and schema settings.
        """

        return remote_api.connection.get_runcard(runcard_name=platform_name).runcard
