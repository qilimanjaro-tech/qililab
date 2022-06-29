"""__init__.py"""
from .components import BusElement
from .components.bus import Bus
from .components.buses import Buses
from .components.schema import Schema
from .platform import Platform
from .platform_manager_db import PlatformManagerDB
from .platform_manager_yaml import PlatformManagerYAML
from .utils import RuncardSchema

PLATFORM_MANAGER_DB = PlatformManagerDB()
PLATFORM_MANAGER_YAML = PlatformManagerYAML()


def build_platform(name: str, database: bool = False) -> Platform:
    """Build platform.

    Args:
        platform_name (str): Platform name.
        database (bool, optional): If True, build platform from database. Defaults to False.

    Returns:
        Platform: Platform object.
    """
    if database:
        raise NotImplementedError
    return PLATFORM_MANAGER_YAML.build(platform_name=name)


def save_platform(platform: Platform, database: bool = False):
    """Save platform.

    Args:
        platform_name (str): Platform name.
        database (bool, optional): If True, save platform to database. Defaults to False.
    """
    if database:
        raise NotImplementedError
    return PLATFORM_MANAGER_YAML.dump(platform=platform)
