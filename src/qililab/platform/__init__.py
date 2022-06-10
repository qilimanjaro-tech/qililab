"""__init__.py"""
from .components.bus import Bus
from .components.buses import Buses
from .components.schema import Schema
from .components.targets.qubit import Qubit
from .components.targets.resonator import Resonator
from .platform import Platform
from .platform_manager_db import PlatformManagerDB
from .platform_manager_yaml import PlatformManagerYAML
from .utils import PlatformSchema

PLATFORM_MANAGER_DB = PlatformManagerDB()
PLATFORM_MANAGER_YAML = PlatformManagerYAML()


def build_platform(platform_name: str, database: bool = False):
    """Build platform.

    Args:
        platform_name (str): Platform name.
        database (bool, optional): If True, build platform from database. Defaults to False.

    Returns:
        _type_: _description_
    """
    if database:
        return PLATFORM_MANAGER_DB.build(platform_name=platform_name)
    return PLATFORM_MANAGER_YAML.build(platform_name=platform_name)
