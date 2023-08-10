"""
This module contains all the methods and classes used to define a Platform, which is a representation
of a laboratory.

.. currentmodule:: qililab

Platform-related methods
~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~build_platform
    ~save_platform

Platform Class
~~~~~~~~~~~~~~~~

.. currentmodule:: qililab.platform

.. autosummary::
    :toctree: api

    ~Platform


Platform Components
~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~Bus
"""
from qiboconnection.api import API

from .components import Bus, BusElement, Buses, Schema
from .platform import Platform
from .platform_manager_db import PlatformManagerDB
from .platform_manager_yaml import PlatformManagerYAML

PLATFORM_MANAGER_DB = PlatformManagerDB()
PLATFORM_MANAGER_YAML = PlatformManagerYAML()


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
    return PLATFORM_MANAGER_YAML.build(platform_name=name, connection=connection)


def save_platform(platform: Platform, database: bool = False):
    """Save platform.

    Args:
        platform_name (str): Platform name.
        database (bool, optional): If True, save platform to database. Defaults to False.
    """
    if database:
        raise NotImplementedError
    return PLATFORM_MANAGER_YAML.dump(platform=platform)
