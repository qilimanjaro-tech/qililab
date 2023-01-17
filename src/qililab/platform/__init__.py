"""__init__.py"""
from qililab.remote_connection import RemoteAPI

from .components import BusElement
from .components.bus import Bus
from .components.buses import Buses
from .components.schema import Schema
from .platform import Platform
from .platform_manager_db import PlatformManagerDB
from .platform_manager_yaml import PlatformManagerYAML

PLATFORM_MANAGER_DB = PlatformManagerDB()
PLATFORM_MANAGER_YAML = PlatformManagerYAML()


def build_platform(name: str, database: bool = False, remote_api: RemoteAPI | None = None) -> Platform:
    """Build platform.

    Args:
        name (str): Platform name.
        database (bool, optional): If True, build platform from database. Defaults to False.
        remote_api (RemoteAPI,  optional):

    Returns:
        Platform: Platform object.
    """
    if database:
        return PLATFORM_MANAGER_DB.build(platform_name=name, remote_api=remote_api)
    return PLATFORM_MANAGER_YAML.build(platform_name=name)


def save_platform(platform: Platform, database: bool = False, remote_api: RemoteAPI = None, description: str = ""):
    """Save platform.

    Args:
        platform (Platform): Platform instance.
        database (bool, optional): If True, save platform to database. Defaults to False.
        remote_api (RemoteAPI, optional): If database, connection with which accessing the database.
        description (str): Short informative description
    """
    if database:
        PLATFORM_MANAGER_DB.dump(platform=platform, remote_api=remote_api, description=description)
    return PLATFORM_MANAGER_YAML.dump(platform=platform)
