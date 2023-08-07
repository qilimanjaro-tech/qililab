"""__init__.py"""
from qiboconnection.api import API

from .components import Bus, BusElement, Buses, Schema
from .platform import Platform
from .platform_manager_db import PlatformManagerDB
from .platform_manager_yaml import PlatformManagerYAML

PLATFORM_MANAGER_DB = PlatformManagerDB()
PLATFORM_MANAGER_YAML = PlatformManagerYAML()
NEW_DRIVERS = False


def build_platform(name: str, connection: API | None = None, database: bool = False) -> Platform:
    """Build platform.

    Args:
        platform_name (str): Platform name.
        database (bool, optional): If True, build platform from database. Defaults to False.

    Returns:
        Platform: Platform object.
    """
    if database:
        raise NotImplementedError
    return PLATFORM_MANAGER_YAML.build(platform_name=name, connection=connection, new_drivers=NEW_DRIVERS)


def save_platform(platform: Platform, database: bool = False):
    """Save platform.

    Args:
        platform_name (str): Platform name.
        database (bool, optional): If True, save platform to database. Defaults to False.
    """
    if database:
        raise NotImplementedError
    return PLATFORM_MANAGER_YAML.dump(platform=platform)


def set_new_drivers_flag(value: bool):
    """Turns on/off the new drivers flag.

    Args:
        value (bool): If True, turns on the new drivers flag. Defaults to False.
    """
    global NEW_DRIVERS  # pylint: disable=C0103
    NEW_DRIVERS = value


def get_new_drivers_flag():
    """Returns the value of the NEW_DRIVERS flag.

    Returns:
        NEW_DRIVERS (bool): If True, the new drivers will be used to build the platform.
    """
    return NEW_DRIVERS
